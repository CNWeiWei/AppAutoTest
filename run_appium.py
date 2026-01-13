#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com,chenwei@zygj.com
@file: test
@date: 2026/1/12 10:21
@desc: 
"""
import subprocess
import time
import os
import sys
import http.client
import socket
import json
from pathlib import Path
from enum import Enum, auto

# --- 核心配置 ---
# 使用 pathlib 获取当前脚本所在的绝对路径
BASE_DIR = Path(__file__).resolve().parent

APPIUM_HOST = "127.0.0.1"
APPIUM_PORT = 4723
# 使用 npm run 确保 APPIUM_HOME=. 变量和本地版本生效
NODE_CMD = f"npm run appium -- -p {APPIUM_PORT}"


class AppiumStatus(Enum):
    """Appium 服务状态枚举"""
    READY = "服务已启动"  # 服务和驱动都加载完成 (HTTP 200 + ready: true)
    INITIALIZING = "驱动正在加载"  # 服务已响应但驱动仍在加载 (HTTP 200 + ready: false)
    CONFLICT = "端口被其他程序占用"  # 端口被其他非 Appium 程序占用
    OFFLINE = "服务未启动"  # 服务未启动
    ERROR = "内部错误"
    UNKNOWN = "未知状态"


def get_appium_status() -> AppiumStatus:
    """深度探测 Appium 状态"""
    conn = None
    try:
        # 1. 端口开启，尝试获取 Appium 状态接口
        conn = http.client.HTTPConnection(APPIUM_HOST, APPIUM_PORT, timeout=2)
        conn.request("GET", "/status")
        response = conn.getresponse()

        if response.status != 200:
            return AppiumStatus.CONFLICT

        data = json.loads(response.read().decode())

        # 2. 解析 Appium 3.x 标准响应结构
        # 即使服务响应了，也要看驱动是否加载完成 (ready 字段)
        is_ready = data.get("value", {}).get("ready")
        return AppiumStatus.READY if is_ready else AppiumStatus.INITIALIZING


    except (socket.error, ConnectionRefusedError):
        # 3. 如果通信拒绝，检查端口是否真的空闲
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(1)
                s.bind((APPIUM_HOST, APPIUM_PORT))
                return AppiumStatus.OFFLINE  # 真正未启动
            except OSError:
                return AppiumStatus.CONFLICT  # 端口被占用但没响应 HTTP
    except (http.client.HTTPException, json.JSONDecodeError):
        return AppiumStatus.CONFLICT
    except Exception as e:
        print(e)
        return AppiumStatus.ERROR
    finally:
        if conn: conn.close()


def start_appium_service():
    """管理 Appium 服务的生命周期"""
    # if check_before_start():
    #     return None
    process = None  # 1. 预先初始化变量，防止作用域错误
    status = get_appium_status()
    match status:  # Python 3.10+ 的模式匹配
        case AppiumStatus.READY:
            print(f"--> [复用] 有效的 Appium 服务已在运行 (Port: {APPIUM_PORT})")
            return None
        case AppiumStatus.INITIALIZING:
            print("⏳ Appium 正在初始化，等待...")
        case AppiumStatus.CONFLICT:
            print(f"\n[!] 错误: 端口 {APPIUM_PORT} 被非 Appium 程序占用。")
            print("=" * 60)
            print("请手动执行以下命令释放端口后重试：")
            if sys.platform == "win32":
                print(
                    f"  CMD: for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :{APPIUM_PORT}') do taskkill /F /PID %a")
            else:
                print(f"  Terminal: lsof -ti:{APPIUM_PORT} | xargs kill -9")
            print("=" * 60)
            sys.exit(1)
        case AppiumStatus.OFFLINE:
            print("🔌 Appium 未启动")
            print(f"🚀 正在准备启动本地 Appium 服务 (Port: {APPIUM_PORT})...")

            # 注入环境变量，确保 Appium 寻找项目本地的驱动
            env_vars = os.environ.copy()
            env_vars["APPIUM_HOME"] = str(BASE_DIR)

            try:
                process = subprocess.Popen(
                    NODE_CMD,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=env_vars,
                    cwd=BASE_DIR
                )

            except Exception as e:
                print(f"❌ 启动过程发生异常: {e}")
                sys.exit(1)
        case _:
            print("Appium 启动异常")
            sys.exit(1)
    # 轮询等待真正就绪
    max_retries = 40
    for i in range(max_retries):
        status = get_appium_status()

        if status == AppiumStatus.READY:
            # 安全打印 PID
            pid_str = f"PID: {process.pid}" if process else "EXTERNAL"
            print(f"✨ Appium 已经完全就绪! ({pid_str})")
            return process

        if status == AppiumStatus.ERROR:
            print("❌ 探测接口发生内部错误（可能是解析失败或严重网络异常），脚本终止。")
            if process: process.terminate()
            sys.exit(1)

        if status == AppiumStatus.INITIALIZING:
            if i % 4 == 0:
                print("...Appium 正在加载驱动/插件，请稍候...")

        if status == AppiumStatus.OFFLINE:
            # 仅当进程是我们启动的（process 不为 None）才检查崩溃(None: 程序正常运行，非None: 程序异常)
            if process and process.poll() is not None:
                print("❌ Appium 进程启动后异常退出。")
                sys.exit(1)

        time.sleep(0.5)

    print("❌ 启动超时：Appium 在规定时间内未完成初始化。")
    if process: process.terminate()
    sys.exit(1)


def stop_appium_service(process):
    """安全关闭服务"""
    if process and process.poll() is None:
        print(f"\n🛑 正在关闭 Appium 服务 (PID: {process.pid})...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("✅ 服务已安全退出。")


if __name__ == "__main__":
    # 使用示例：作为一个上下文管理器或简单的生命周期示例
    appium_proc = None
    try:
        appium_proc = start_appium_service()
        print(f"\n[项目路径] {BASE_DIR}")
        print("\n[提示] 现在可以手动或通过其他脚本运行测试用例。")
        print("[提示] 按下 Ctrl+C 可停止由本脚本启动的服务。")

        # 保持运行，直到手动停止（在实际测试框架中，这里会被替换为测试执行逻辑）
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        stop_appium_service(appium_proc)
