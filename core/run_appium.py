#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: run_appium
@date: 2026/1/12 10:21
@desc: 
"""
import functools
import logging
import signal
import subprocess
import time
import os
import sys
import http.client
import socket
import json

from typing import List

from core.settings import BASE_DIR, APPIUM_HOST, APPIUM_PORT, MAX_RETRIES
from core.enums import AppiumStatus, ServiceRole

logger = logging.getLogger(__name__)


# 使用 npm run 确保 APPIUM_HOME=. 变量和本地版本生效
# NODE_CMD = f"npm run appium -- -p {APPIUM_PORT}"
# --- 1. 异常体系设计 (精确分类) ---
class AppiumStartupError(Exception):
    """所有 Appium 启动相关异常的基类"""
    pass


class AppiumPortConflictError(AppiumStartupError):
    """端口被其他非 Appium 程序占用"""
    pass


class AppiumProcessCrashError(AppiumStartupError):
    """进程启动后立即崩溃或在运行中意外退出"""
    pass


class AppiumTimeoutError(AppiumStartupError):
    """服务在规定时间内未进入 READY 状态"""
    pass


class AppiumInternalError(AppiumStartupError):
    """探测接口返回了无法解析的数据或网络异常"""
    pass


def resolve_appium_command(host: str, port: int | str) -> List[str]:
    """
       解析 Appium 可执行文件的绝对路径。
       优先查找项目 node_modules 下的本地安装版本，避免 npm 包装层带来的信号传递问题。

       :return: 用于 subprocess 的命令列表
       :raises SystemExit: 如果找不到 Appium 执行文件
       """
    bin_name = "appium.cmd" if sys.platform == "win32" else "appium"
    appium_bin = BASE_DIR / "node_modules" / ".bin" / bin_name

    if not appium_bin.exists():
        # 报错提示：找不到本地 Appium，引导用户安装
        logger.error(f"\n错误: 在路径 {appium_bin} 未找到 Appium 执行文件。")
        logger.info("请确保已在项目目录下执行过: npm install appium")
        sys.exit(1)
    # 返回执行列表（用于 shell=False）--address 127.0.0.1 --port 4723 appium -a 127.0.0.1 -p 4723
    return [str(appium_bin), "--address", host, "--port", str(port)]


# 移除全局调用，防止 import 时因找不到 appium 而直接退出
# APP_CMD_LIST = resolve_appium_command()

def _cleanup_process_tree(process: subprocess.Popen = None) -> None:
    """
    核心清理逻辑：跨平台递归终止进程树。

    :param process: subprocess.Popen 对象
    """
    if not process or process.poll() is not None:
        return
    pid = process.pid
    logger.info(f"正在关闭 Appium 进程树 (PID: {pid})...")
    try:
        if sys.platform == "win32":
            # Windows 下使用 taskkill 强制关闭进程树 /T
            subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # Unix/Linux: 获取进程组 ID 并发送终止信号
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 5秒没关掉，强制杀掉整个进程组
                # 如果 SIGTERM 不起作用，直接 SIGKILL 整个组
                logger.warning(f"进程 {pid} 未响应 SIGTERM，发送 SIGKILL...")
                os.killpg(pgid, signal.SIGKILL)
        logger.info("Appium 服务已停止,相关进程已安全退出。")
    except Exception as e:
        logger.error(f"停止服务时发生异常: {e}")
        try:
            process.kill()
            logger.warning(f"已强制杀死进程: {e}")
        except Exception as e:
            logger.debug(f"强制杀死进程失败 (可能已退出): {e}")
            # 这里通常保持安静，因为我们已经尝试过清理了
    logger.info("服务已完全清理。")


class AppiumService:
    """Appium 服务实例封装，用于管理服务生命周期"""

    def __init__(self, role: ServiceRole, host: str, port: int | str, process: subprocess.Popen = None):
        self.role = role
        self.host = host
        self.port = port
        self.process = process

    def __repr__(self):
        return f"<AppiumService 角色='{self.role.value}' 地址=http://{self.host}:{self.port}>"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def stop(self):
        """统一停止接口：根据角色决定是否关闭进程"""
        match self.role:
            case ServiceRole.EXTERNAL:
                logger.info(f"--> [角色: {self.role.value}] 脚本退出，保留外部服务运行。")
                return
            case ServiceRole.MANAGED:
                logger.info(f"正在关闭托管的 Appium 服务 (PID: {self.process.pid})...")
                _cleanup_process_tree(self.process)
                self.process = None
            case ServiceRole.NULL:
                logger.info(f"--> [角色: {self.role.value}] 无需执行清理。")


def _check_port_availability(host: str, port: int) -> AppiumStatus:
    """辅助函数：检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.settimeout(1)
            # 尝试绑定端口，如果成功说明端口空闲
            sock.bind((host, port))
            return AppiumStatus.OFFLINE  # 真正未启动
        except OSError:
            # 绑定失败，说明端口被占用，但此前 HTTP 请求失败，说明不是 Appium
            return AppiumStatus.CONFLICT  # 端口被占用但没响应 HTTP


def get_appium_status(host: str, port: int | str) -> AppiumStatus:
    """
    检测 Appium 服务当前状态。

    逻辑：
    1. 尝试 HTTP 连接 /status 接口。
    2. 如果连接成功，检查 ready 字段。
    3. 如果连接被拒绝，尝试绑定端口以确认端口是否真正空闲。

    :return: AppiumStatus 枚举
    """
    connection = None
    port = int(port)  # 确保端口是整数
    try:
        # 1. 端口开启，尝试获取 Appium 状态接口
        connection = http.client.HTTPConnection(host, port, timeout=2)
        connection.request("GET", "/status")
        response = connection.getresponse()

        if response.status != 200:
            return AppiumStatus.CONFLICT

        data = json.loads(response.read().decode('utf-8'))

        # 2. 解析 Appium 3.x 标准响应结构
        # 即使服务响应了，也要看驱动是否加载完成 (ready 字段)
        is_ready = data.get("value", {}).get("ready")
        return AppiumStatus.READY if is_ready else AppiumStatus.INITIALIZING

    except (socket.error, ConnectionRefusedError):
        # 3. 如果通信拒绝，检查端口是否被占用
        return _check_port_availability(host, port)
    except (http.client.HTTPException, json.JSONDecodeError):
        return AppiumStatus.UNKNOWN
    except Exception as e:
        logger.error(f"状态检测异常: {e}")
        return AppiumStatus.ERROR
    finally:
        if connection: connection.close()


def start_appium_service(host: str = APPIUM_HOST, port: int | str = APPIUM_PORT) -> AppiumService:
    """
    管理 Appium 服务的生命周期
    如果服务未启动，则启动本地服务；如果已启动，则复用。

    :return: AppiumService 对象
    """
    process = None  # 1. 预先初始化变量，防止作用域错误
    is_managed = False
    # 轮询等待真正就绪
    # 延迟获取命令，确保只在真正需要启动服务时检查环境
    cmd_args = resolve_appium_command(host, port)
    try:
        for i in range(MAX_RETRIES):
            status = get_appium_status(host, port)
            match status:  # Python 3.10+ 的模式匹配
                case AppiumStatus.READY:
                    if is_managed:
                        # 安全打印 PID
                        pid_info = f"PID: {process.pid}" if process else "EXTERNAL"
                        logger.info(f"Appium 服务启动成功! ({pid_info})")
                        return AppiumService(ServiceRole.MANAGED, host, port, process)
                    else:
                        logger.info(f"--> [复用] 有效的 Appium 服务已在运行 (http://{host}:{port})")
                        logger.info("--> [注意] 脚本退出时将保留该服务，不会将其关闭。")
                        return AppiumService(ServiceRole.EXTERNAL, host, port, process)
                case AppiumStatus.CONFLICT:
                    _handle_port_conflict(port)
                case AppiumStatus.OFFLINE:
                    if not is_managed:
                        process = _spawn_appium_process(cmd_args)
                        is_managed = True

                    elif process and process.poll() is not None:
                        raise AppiumProcessCrashError("Appium 进程启动后异常退出。")

                case AppiumStatus.INITIALIZING:
                    if is_managed and process and process.poll() is not None:
                        raise AppiumProcessCrashError("Appium 在初始化期间崩溃。")

                    if i % 4 == 0:  # 每 2 秒提醒一次，避免刷屏
                        logger.info("Appium 正在加载驱动/插件，请稍候...")
                case AppiumStatus.ERROR:
                    raise AppiumInternalError("探测接口发生内部错误（可能是解析失败或严重网络异常），脚本终止。")
                case _:
                    raise AppiumInternalError("Appium 启动异常")

            time.sleep(0.5)

        raise AppiumTimeoutError("启动超时：Appium 在规定时间内未完成初始化。")
    except AppiumStartupError as e:
        if process:
            logger.warning(f"检测到启动阶段异常，正在回收进程资源 (PID: {process.pid})...")
            _cleanup_process_tree(process)
        # 将清理后的异常继续向上传递给装饰器
        raise e


def _handle_port_conflict(port: int | str) -> AppiumStartupError:
    hand = f"端口 {port} 被其他程序占用,建议清理命令：\n"
    if sys.platform == "win32":
        raise AppiumPortConflictError(
            f"{hand}CMD: for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :{port}') do taskkill /F /PID %a")
    else:
        raise AppiumPortConflictError(f"{hand}Unix: lsof -ti:{port} | xargs kill -9")


def _spawn_appium_process(cmd_args: List[str]) -> subprocess.Popen:
    """启动 Appium 子进程"""
    logger.info(f"正在启动本地 Appium 服务...")

    # 注入环境变量，确保 Appium 寻找项目本地的驱动
    env_vars = os.environ.copy()
    env_vars["APPIUM_HOME"] = str(BASE_DIR)

    try:
        return subprocess.Popen(
            cmd_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env_vars,
            cwd=BASE_DIR,
            # Windows 和 Linux/Mac 的处理方式不同
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            preexec_fn=os.setsid if sys.platform != "win32" else None
        )
    except Exception as e:
        logger.error(f"启动过程发生异常: {e}")
        sys.exit(1)


def stop_appium_service(service: AppiumService):
    """
    停止 Appium 服务。
    如果已经使用了 with 语句，通常不需要手动调用此函数。
    :param service: AppiumService 对象
    """
    if service:
        service.stop()


# --- 装饰器实现 ---
def managed_appium(host: str = APPIUM_HOST, port: int | str = APPIUM_PORT):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. start_appium_service 返回 AppiumService 实例
            # 2. with 触发 __enter__
            # 3. 结束或异常触发 __exit__ -> stop()
            with start_appium_service(host, port) as service:
                logger.debug(f"装饰器环境就绪: {service}")
                return func(*args, **kwargs)

        return wrapper

    return decorator


if __name__ == "__main__":
    # 使用示例：作为一个上下文管理器或简单的生命周期示例
    appium_service = None
    try:
        appium_service = start_appium_service()
        print(f"\n[项目路径] {BASE_DIR}")
        print(f"[服务状态] Appium 运行中...)")
        print("[操作提示] 按 Ctrl+C 停止服务...")

        # 保持运行，直到手动停止（在实际测试框架中，这里会被替换为测试执行逻辑）
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n收到停止信号...")
    finally:
        stop_appium_service(appium_service)
