#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: test
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
from enum import Enum
from typing import List

from core.settings import BASE_DIR, APPIUM_HOST, APPIUM_PORT, MAX_RETRIES

logger = logging.getLogger(__name__)


# 使用 npm run 确保 APPIUM_HOME=. 变量和本地版本生效
# NODE_CMD = f"npm run appium -- -p {APPIUM_PORT}"


class AppiumStatus(Enum):
    """Appium 服务状态枚举"""
    READY = "服务已启动"  # 服务和驱动都加载完成 (HTTP 200 + ready: true)
    INITIALIZING = "驱动正在加载"  # 服务已响应但驱动仍在加载 (HTTP 200 + ready: false)
    CONFLICT = "端口被其他程序占用"  # 端口被其他非 Appium 程序占用
    OFFLINE = "服务未启动"  # 服务未启动
    ERROR = "内部错误"
    UNKNOWN = "未知状态"


class ServiceRole(Enum):
    """服务角色枚举：定义服务的所有权和生命周期"""
    MANAGED = "由脚本启动 (托管模式)"  # 由本脚本启动，负责清理
    EXTERNAL = "复用外部服务 (共享模式)"  # 复用现有服务，不负责清理
    NULL = "无效服务 (空模式)"  # 无效或未初始化的服务


def resolve_appium_command() -> List[str]:
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
    # 返回执行列表（用于 shell=False）
    return [str(appium_bin), "-p", str(APPIUM_PORT)]


# 移除全局调用，防止 import 时因找不到 appium 而直接退出
# APP_CMD_LIST = resolve_appium_command()

def _cleanup_process_tree(process: subprocess.Popen = None) -> None:
    """
    核心清理逻辑：跨平台递归终止进程树。

    :param process: subprocess.Popen 对象
    """
    if not process or process.poll() is not None:
        return
    logger.info(f"正在关闭 Appium 进程树 (PID: {process.pid})...")
    try:
        if sys.platform == "win32":
            # Windows 下使用 taskkill 强制关闭进程树 /T
            subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(process.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # Unix/Linux: 获取进程组 ID 并发送终止信号
            pgid = os.getpgid(process.pid)
            os.killpg(pgid, signal.SIGTERM)

        process.wait(timeout=5)
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

    def __init__(self, role: ServiceRole, process: subprocess.Popen = None):
        self.role = role
        self.process = process

    def stop(self):
        """统一停止接口：根据角色决定是否关闭进程"""
        match self.role:
            case ServiceRole.EXTERNAL:
                logger.info(f"--> [角色: {self.role.value}] 脚本退出，保留外部服务运行。")
                return
            case ServiceRole.MANAGED:
                _cleanup_process_tree(self.process)
            case ServiceRole.NULL:
                logger.info(f"--> [角色: {self.role.value}] 无需执行清理。")

    def __repr__(self):
        return f"<AppiumService 角色='{self.role.value}' 端口={APPIUM_PORT}>"


def _check_port_availability() -> AppiumStatus:
    """辅助函数：检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.settimeout(1)
            # 尝试绑定端口，如果成功说明端口空闲
            sock.bind((APPIUM_HOST, APPIUM_PORT))
            return AppiumStatus.OFFLINE  # 真正未启动
        except OSError:
            # 绑定失败，说明端口被占用，但此前 HTTP 请求失败，说明不是 Appium
            return AppiumStatus.CONFLICT  # 端口被占用但没响应 HTTP


def get_appium_status() -> AppiumStatus:
    """
    检测 Appium 服务当前状态。

    逻辑：
    1. 尝试 HTTP 连接 /status 接口。
    2. 如果连接成功，检查 ready 字段。
    3. 如果连接被拒绝，尝试绑定端口以确认端口是否真正空闲。

    :return: AppiumStatus 枚举
    """
    connection = None
    try:
        # 1. 端口开启，尝试获取 Appium 状态接口
        connection = http.client.HTTPConnection(APPIUM_HOST, APPIUM_PORT, timeout=2)
        connection.request("GET", "/status")
        response = connection.getresponse()

        if response.status != 200:
            return AppiumStatus.CONFLICT

        data = json.loads(response.read().decode())

        # 2. 解析 Appium 3.x 标准响应结构
        # 即使服务响应了，也要看驱动是否加载完成 (ready 字段)
        is_ready = data.get("value", {}).get("ready")
        return AppiumStatus.READY if is_ready else AppiumStatus.INITIALIZING

    except (socket.error, ConnectionRefusedError):
        # 3. 如果通信拒绝，检查端口是否真的空闲
        return _check_port_availability()
    except (http.client.HTTPException, json.JSONDecodeError):
        return AppiumStatus.UNKNOWN
    except Exception as e:
        logger.error(f"状态检测异常: {e}")
        return AppiumStatus.ERROR
    finally:
        if connection: connection.close()


def start_appium_service() -> AppiumService:
    """
    管理 Appium 服务的生命周期
    如果服务未启动，则启动本地服务；如果已启动，则复用。

    :return: AppiumService 对象
    """
    process = None  # 1. 预先初始化变量，防止作用域错误
    is_managed = False
    # 轮询等待真正就绪
    # 延迟获取命令，确保只在真正需要启动服务时检查环境
    cmd_args = resolve_appium_command()

    for i in range(MAX_RETRIES):
        status = get_appium_status()
        match status:  # Python 3.10+ 的模式匹配
            case AppiumStatus.READY:
                if is_managed:
                    # 安全打印 PID
                    pid_info = f"PID: {process.pid}" if process else "EXTERNAL"
                    logger.info(f"Appium 服务启动成功! ({pid_info})")
                    return AppiumService(ServiceRole.MANAGED, process)
                else:
                    logger.info(f"--> [复用] 有效的 Appium 服务已在运行 (Port: {APPIUM_PORT})")
                    logger.info("--> [注意] 脚本退出时将保留该服务，不会将其关闭。")
                    return AppiumService(ServiceRole.EXTERNAL, process)
            case AppiumStatus.CONFLICT:
                _handle_port_conflict()
            case AppiumStatus.OFFLINE:
                if not is_managed:
                    process = _spawn_appium_process(cmd_args)
                    is_managed = True

                else:
                    if process and process.poll() is not None:
                        logger.warning("Appium 进程启动后异常退出。")
                        sys.exit(1)
            case AppiumStatus.INITIALIZING:
                if is_managed and process and process.poll() is not None:
                    logger.warning("Appium 在初始化期间崩溃。")
                    _cleanup_process_tree(process)
                    sys.exit(1)
                if i % 4 == 0:  # 每 2 秒提醒一次，避免刷屏
                    logger.info("Appium 正在加载驱动/插件，请稍候...")
            case AppiumStatus.ERROR:
                logger.error("探测接口发生内部错误（可能是解析失败或严重网络异常），脚本终止。")
                if is_managed and process:
                    _cleanup_process_tree(process)
                sys.exit(1)
            case _:
                logger.error("Appium 启动异常")
                sys.exit(1)

        time.sleep(0.5)

    logger.warning("启动超时：Appium 在规定时间内未完成初始化。")
    _cleanup_process_tree(process)
    sys.exit(1)


def _handle_port_conflict():
    logger.warning(f"\n[!] 错误: 端口 {APPIUM_PORT} 被占用。")
    logger.info("=" * 60)
    logger.info("请手动执行以下命令释放端口后重试：")
    if sys.platform == "win32":
        logger.info(
            f"  CMD: for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :{APPIUM_PORT}') do taskkill /F /PID %a")
    else:
        logger.info(f"  Terminal: lsof -ti:{APPIUM_PORT} | xargs kill -9")
    logger.info("=" * 60)
    sys.exit(1)


def _spawn_appium_process(cmd_args: List[str]) -> subprocess.Popen:
    """启动 Appium 子进程"""
    logger.info(f"正在启动本地 Appium 服务 (Port: {APPIUM_PORT})...")

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
    :param service: AppiumService 对象
    """
    service.stop()


# --- 装饰器实现 ---
def with_appium(func):
    """
    装饰器：在函数执行前后自动启动和停止 Appium 服务。
    适用于简单的脚本或调试场景。
    :param func: 需要包装的函数
    :return: 包装后的函数
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        service = start_appium_service()
        try:
            # return func(service, *args, **kwargs)
            return func(*args, **kwargs)
        finally:
            service.stop()

    return wrapper


if __name__ == "__main__":
    # 使用示例：作为一个上下文管理器或简单的生命周期示例
    appium_service = None
    try:
        appium_service = start_appium_service()
        print(f"\n[项目路径] {BASE_DIR}")
        print(f"[服务状态] Appium 运行中 (Port: {APPIUM_PORT})")
        print("[操作提示] 按 Ctrl+C 停止服务...")

        # 保持运行，直到手动停止（在实际测试框架中，这里会被替换为测试执行逻辑）
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n收到停止信号...")
    finally:
        stop_appium_service(appium_service)
