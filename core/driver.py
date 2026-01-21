#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com,chenwei@zygj.com
@file: driver
@date: 2026/1/16 10:49
@desc: 
"""
import logging
from enum import Enum
from typing import Optional, Type, TypeVar
from time import sleep

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from appium.options.common.base import AppiumOptions
from appium.webdriver.webdriver import ExtensionBase
from appium.webdriver.client_config import AppiumClientConfig
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.bidi.cdp import session_context

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

from utils.finder import by_converter
from settings import IMPLICIT_WAIT_TIMEOUT, EXPLICIT_WAIT_TIMEOUT

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AppPlatform(Enum):
    ANDROID = "android"
    IOS = "ios"


class CoreDriver:
    def __init__(self):
        self.driver: Optional[webdriver.Remote] = None
        self._host = "127.0.0.1"
        self._port = 4723

    def server_config(self, host: str = "127.0.0.1", port: int = 4723):
        """配置服务端信息"""
        self._host = host
        self._port = port
        logger.info(f"Appium Server 指向 -> {self._host}:{self._port}")

    def connect(self, platform: str | AppPlatform, caps: dict,
                extensions: list[Type[ExtensionBase]] | None = None,
                client_config: AppiumClientConfig | None = None) -> 'CoreDriver':
        """
        参照 KeyWordDriver 逻辑，但强化了配置校验和异常处理
        """
        # 1. 统一格式化平台名称
        platform_name = platform.value if isinstance(platform, AppPlatform) else platform.lower().strip()
        url = f"http://{self._host}:{self._port}"

        # 2. 预校验：如果已经有 driver 正在运行，先清理（防止 Session 冲突）
        if self.driver:
            logger.warning("发现旧的 Driver 实例尚未关闭，正在强制重置...")
            self.quit()

        try:
            # 3. 匹配平台并加载 Options
            match platform_name:
                case AppPlatform.ANDROID.value:
                    logger.info(f"正在初始化 Android 会话...")
                    options: AppiumOptions = UiAutomator2Options().load_capabilities(caps)

                case AppPlatform.IOS.value:
                    logger.info(f"正在初始化 iOS 会话...")
                    options: AppiumOptions = XCUITestOptions().load_capabilities(caps)

                case _:
                    # 优化：不再默认返回 Android，而是显式报错 (Fail Fast)
                    msg = f"不支持的平台类型: [{platform_name}]。当前仅支持: [android, ios]"
                    logger.error(msg)
                    raise ValueError(msg)

            # 4. 创建连接
            self.driver = webdriver.Remote(
                command_executor=url,
                options=options,
                extensions=extensions,
                client_config=client_config
            )

            logger.info(f"已成功连接到 {platform_name.upper()} 设备 (SessionID: {self.driver.session_id})")
            return self

        except Exception as e:
            logger.error(f"驱动连接失败！底层错误信息: {e}")
            # 确保失败后清理现场
            self.driver = None
            raise ConnectionError(f"无法连接到 Appium 服务，请检查端口 {self._port} 或设备状态。") from e

    # --- 核心操作 ---
    def find_element(self, by, value, timeout=10):
        """内部通用查找（显式等待）"""
        by = by_converter(by)
        mark = (by, value)

        return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(mark))

    def delay(self, timeout: int | float):
        sleep(timeout)
        return self

    def implicit_wait(self, timeout: float = IMPLICIT_WAIT_TIMEOUT, *args, **kwargs) -> None:
        """
        隐式等待
        :param timeout: 超时时间
        :param args:
        :param kwargs:
        :return:
        """
        self.driver.implicitly_wait(timeout)

    def explicit_wait(self, method: T, timeout: float = EXPLICIT_WAIT_TIMEOUT, *args, **kwargs):
        """
        显示等待
        :param method: 可调用对象名
        :param timeout: 超时时间
        :param args:
        :param kwargs:
        :return:
        """

        try:
            if isinstance(method, str):
                # method = custom_ec.get(method, (lambda _: False))
                method = lambda _: False

            logger.info(f"预期条件: {method.__name__}")

            return WebDriverWait(self.driver, timeout).until(method)
        except TypeError as te:
            logger.error(f"显示等待异常: {te}")
            # self.driver.quit()
            raise te

    def page_load_timeout(self, timeout: float, *args, **kwargs) -> None:
        self.driver.set_page_load_timeout(timeout)

    def click(self, by, value, timeout=10) -> 'CoreDriver':
        by = by_converter(by)
        mark = (by, value)
        logger.info(f"点击: {mark}")
        method = EC.element_to_be_clickable(mark)
        self.explicit_wait(method, timeout).click()
        return self

    def clear(self, by, value, *args, **kwargs):

        by = by_converter(by)
        mark = (by, value)
        method = EC.visibility_of_element_located(mark)

        self.explicit_wait(method).clear()

        # self.driver.find_element(by, value).clear()

    def input(self, by, value, text, timeout=10) -> 'CoreDriver':
        by = by_converter(by)
        mark = (by, value)
        method = EC.visibility_of_element_located(mark)

        self.explicit_wait(method, timeout).send_keys(text)
        return self

    def get_text(self, by, value, *args, **kwargs):
        """
        获取元素文本
        :param by:
        :param value:
        :param args:
        :param kwargs:
        :return:
        """
        by = by_converter(by)
        mark = (by, value)
        method = EC.visibility_of_element_located(mark)

        text = self.explicit_wait(method).text
        logger.info(f"获取到的文本{text}")
        return text

    def get_session_id(self):

        return self.driver.session_id

    # --- 移动端特有：方向滑动 ---
    def swipe_to(self, direction: str = "up", duration: int = 1000) -> 'CoreDriver':
        """
        封装方向滑动 (W3C Actions 兼容版)
        :param direction: 滑动方向 up/down/left/right
        :param duration: 滑动持续时间 (ms)
        :return: self
        """
        # 每次获取屏幕尺寸以适应旋转
        size = self.driver.get_window_size()
        w, h = size['width'], size['height']

        # 定义滑动坐标 (避开边缘区域)
        coords = {
            "up":    (w * 0.5, h * 0.8, w * 0.5, h * 0.2),
            "down":  (w * 0.5, h * 0.2, w * 0.5, h * 0.8),
            "left":  (w * 0.9, h * 0.5, w * 0.1, h * 0.5),
            "right": (w * 0.1, h * 0.5, w * 0.9, h * 0.5)
        }
        start_x, start_y, end_x, end_y = coords.get(direction.lower(), coords["up"])
        logger.info(f"执行滑动: {direction} ({start_x}, {start_y}) -> ({end_x}, {end_y})")

        # 使用 W3C ActionChains 替代已废弃的 driver.swipe
        actions = ActionChains(self.driver)
        # 覆盖默认的鼠标输入为触摸输入
        actions.w3c_actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
        
        actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(duration / 1000)  # pause 单位为秒
        actions.w3c_actions.pointer_action.move_to_location(end_x, end_y)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

        return self

    # --- 断言逻辑 ---
    def assert_text(self, by, value, expected_text) -> 'CoreDriver':
        actual = self.get_text(by, value)
        assert actual == expected_text, f"断言失败: 期望 {expected_text}, 实际 {actual}"
        logger.info(f"断言通过: 文本匹配 '{actual}'")
        return self

    def quit(self):
        """安全退出"""
        if self.driver:
            try:
                # 获取 session_id 用于日志追踪
                sid = self.driver.session_id
                self.driver.quit()
                logger.info(f"已安全断开连接 (Session: {sid})")
            except Exception as e:
                logger.warning(f"断开连接时发生异常 (可能服务已预先关闭): {e}")
            finally:
                self.driver = None
        else:
            logger.debug("没有正在运行的 Driver 实例需要关闭。")

    @property
    def is_alive(self) -> bool:
        """判断当前驱动是否可用"""
        return self.driver is not None and self.driver.session_id is not None
