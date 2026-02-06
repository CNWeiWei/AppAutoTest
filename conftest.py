#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: conftest
@date: 2026/1/16 10:52
@desc: Pytest 核心配置与 Fixture 管理
"""
import logging
import secrets
from pathlib import Path
from typing import Generator, Any

import pytest
import allure

from core.run_appium import start_appium_service, stop_appium_service
from core.driver import CoreDriver
from core.settings import APPIUM_HOST, APPIUM_PORT
from core.config_loader import get_caps


# 注册命令行参数
def pytest_addoption(parser: Any) -> None:
    """
    注册自定义命令行参数
    :param parser: Pytest 参数解析器对象
    """
    parser.addoption("--platform", action="store", default="Android", help="目标平台: Android or IOS")
    parser.addoption("--udid", action="store", default=None, help="设备唯一标识")
    parser.addoption("--host", action="store", default=APPIUM_HOST, help="Appium Server Host")
    parser.addoption("--port", action="store", default=str(APPIUM_PORT), help="Appium Server Port")


@pytest.fixture(scope="session")
def app_server(request: pytest.FixtureRequest) -> Generator[Any, None, None]:
    """
    第一层：管理 Appium Server 进程。
    :param request: Pytest 请求对象
    :return: Appium 服务进程实例
    """
    # 获取命令行参数
    host = request.config.getoption("--host")
    port = int(request.config.getoption("--port"))

    service = start_appium_service(host, port)
    yield service
    stop_appium_service(service)


@pytest.fixture(scope="session")
def driver_session(request: pytest.FixtureRequest, app_server: Any) -> Generator[CoreDriver, None, None]:
    """
    第二层：全局单例 Driver 管理 (Session Scope)。
    负责创建和销毁 Driver，整个测试过程只启动一次 App。
    :param request: Pytest 请求对象
    :param app_server: Appium 服务 fixture 依赖
    :return: CoreDriver 实例
    """
    platform = request.config.getoption("--platform")
    ud_id = request.config.getoption("--udid")
    host = request.config.getoption("--host")
    port = int(request.config.getoption("--port"))

    # 1. 获取基础 Caps
    caps = get_caps(platform)

    # 2. 动态注入参数
    if ud_id: caps["udid"] = ud_id

    # 将最终生效的 caps 存入 pytest 配置，方便报告读取
    request.config._final_caps = caps

    # 3. 初始化 Driver
    app_helper = CoreDriver()
    app_helper.server_config(host=host, port=port)

    try:
        app_helper.connect(platform=platform, caps=caps)
    except Exception as e:
        pytest.exit(f"无法初始化 Driver: {e}")

    yield app_helper

    # 4. 清理
    app_helper.quit()


@pytest.fixture(scope="function")
def driver(driver_session: CoreDriver) -> Generator[Any, None, None]:
    """
    第三层：用例级 Driver 注入。
    每个用例直接获取已存在的 Driver 实例。
    可以在这里添加 reset_app() 逻辑，确保用例间独立性。
    :param driver_session: CoreDriver 会话实例
    :return: 原始 Appium Driver 对象 (webdriver.Remote)
    """
    # 可选：如果需要在每个用例前重置 App 状态
    # driver_session.driver.reset() 
    yield driver_session.driver


def pytest_exception_interact(node: Any, call: Any, report: Any) -> None:
    """
    当测试用例抛出异常（断言失败或代码报错）时，Pytest 会调用这个钩子。
    我们在这里手动把错误信息喂给 logging。
    :param node: 测试节点
    :param call: 调用信息
    :param report: 测试报告
    """
    logger = logging.getLogger("pytest")

    if report.failed:
        # 获取详细的错误堆栈（包含 assert 的对比信息）
        # long,short,no-locals
        exc_info = call.excinfo.getrepr(style='short')
        screenshot_name = f"异常截图_{secrets.token_hex(4)}"

        logger.error(f"\n{'=' * 40} TEST FAILED {'=' * 40}\n"
                     f"Node ID: {node.nodeid}\n"
                     f"截图名称: {screenshot_name}\n"
                     f"详细错误信息:\n{exc_info}"
                     )

        # 尝试获取 driver_session (CoreDriver 实例)
        if "driver_session" in node.funcargs:
            helper = node.funcargs["driver_session"]
            try:
                # 截图并附加到 Allure
                screenshot_bytes = helper.driver.get_screenshot_as_png()
                allure.attach(
                    screenshot_bytes,
                    name=screenshot_name,
                    attachment_type=allure.attachment_type.PNG
                )
            except Exception as e:
                logger.error(f"执行异常截图失败: {e}")
        logger.error("=" * 93 + "\n")


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """
    测试会话结束时，收集环境信息到 Allure 报告
    :param session: Pytest 会话对象
    :param exitstatus: 退出状态码
    """
    match exitstatus:
        case pytest.ExitCode.OK:
            logging.info("测试全部通过！")
        case pytest.ExitCode.TESTS_FAILED:
            logging.warning("部分测试用例执行失败，请检查报告。")
        case pytest.ExitCode.INTERRUPTED:
            logging.error("测试被用户手动中断（Ctrl+C）。")
        case pytest.ExitCode.INTERNAL_ERROR:
            logging.critical("Pytest 发生内部错误！")
        case pytest.ExitCode.USAGE_ERROR:
            logging.error("Pytest 命令行参数错误或用法不当。")
        case pytest.ExitCode.NO_TESTS_COLLECTED:
            logging.warning("未发现任何测试用例。")
        case _:
            logging.error(f"未知错误状态码: {exitstatus}")

    report_dir = session.config.getoption("--alluredir")
    final_caps = getattr(session.config, "_final_caps", {})
    if not report_dir:
        return
    report_path = Path(report_dir)
    # 收集环境信息
    env_info = {
        "Platform": session.config.getoption("--platform"),
        "UDID": final_caps.get("udid") or session.config.getoption("--udid") or "未指定",
        "Host": session.config.getoption("--host"),
        "Python": "3.11+"
    }

    try:
        if not report_path.exists():
            report_path.mkdir(parents=True, exist_ok=True)
        # 生成 environment.properties 文件
        env_file = report_path / "environment.properties"
        with env_file.open("w", encoding="utf-8") as f:
            for k, v in env_info.items():
                f.write(f"{k}={v}\n")
        logging.info("Allure 环境信息已生成。")
    except Exception as e:
        logging.error(f"无法写入环境属性: {e}")
