#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: conftest
@date: 2026/1/16 10:52
@desc: 
"""
import logging
import secrets

import allure
import pytest
from core.run_appium import start_appium_service, stop_appium_service
from core.driver import CoreDriver
from utils.dirs_manager import ensure_dirs_ok


def pytest_configure(config):
    """
    Pytest 钩子函数：在测试收集开始前执行
    """
    # ensure_dirs_ok()
    ...


@pytest.fixture(scope="session")
def app_server():
    """
    第一层：管理 Appium Server 进程。
    利用start_appium_service 里的 40 次轮询和 sys.exit(1) 逻辑。
    """
    # 启动服务
    service = start_appium_service()
    yield service
    # 所有测试结束，清理进程
    stop_appium_service(service)


@pytest.fixture(scope="module")
def driver(app_server):
    """
    第二层：管理 WebDriver 会话。
    依赖 app_server，确保服务 Ready 后才创建连接。
    """
    # 实例化你提供的类结构
    app_helper = CoreDriver()
    caps = {
        "platformName": "Android",
        "automationName": "uiautomator2",
        "deviceName": "Android",
        "appPackage": "com.manu.wanandroid",
        # "appPackage": "com.bocionline.ibmp",
        "appActivity": "com.manu.wanandroid.ui.main.activity.MainActivity",
        # "appActivity": "com.bocionline.ibmp.app.main.launcher.LauncherActivity",
        "noReset": False,  # 不清除应用数据
        "newCommandTimeout": 60
    }
    # 连接并获取原生 driver 实例
    # 这里可以根据需要扩展，比如通过命令行参数选择平台
    app_helper.connect(platform="android", caps=caps)

    yield app_helper.driver

    # 用例结束，只关 session，不关 server
    app_helper.quit()


def pytest_exception_interact(node, call, report):
    """
    当测试用例抛出异常（断言失败或代码报错）时，Pytest 会调用这个钩子。
    我们在这里手动把错误信息喂给 logging。
    """
    # 获取名为 'Error' 的记录器，它会遵循 pytest.ini 中的 log_file 配置
    logger = logging.getLogger("pytest")

    if report.failed:
        # 获取详细的错误堆栈（包含 assert 的对比信息）
        # long,short,no-locals
        exc_info = call.excinfo.getrepr(style='short')
        screenshot_name = f"异常截图_{secrets.token_hex(4)}"

        logger.error("\n" + "=" * 40 + " TEST FAILED " + "=" * 40)
        logger.error(f"Node ID: {node.nodeid}")
        logger.error(f"截图名称: {screenshot_name}")
        logger.error(f"详细错误信息如下:\n{exc_info}")

        # 3. 自动截图：尝试从 fixture 中获取 driver
        # node.funcargs 包含了当前测试用例请求的所有 fixture 实例
        driver = node.funcargs.get("driver")
        if driver:
            try:
                # 同时保存到 Allure 和本地（如果你需要本地有一份备份）
                screenshot_data = driver.get_screenshot_as_png()
                allure.attach(
                    screenshot_data,
                    name=name,
                    attachment_type=allure.attachment_type.PNG
                )
            except Exception as e:
                logger.error(f"执行异常截图失败: {e}")
        logger.error("=" * 93 + "\n")
