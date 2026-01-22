#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com,chenwei@zygj.com
@file: driver
@date: 2026/1/16 10:49
@desc: Appium 核心驱动封装，提供统一的 API 用于 Appium 会话管理和元素操作。
"""
import logging
from typing import Optional, Type, TypeVar, Union, Callable
from time import sleep

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from appium.options.common.base import AppiumOptions
from appium.webdriver.webdriver import ExtensionBase
from appium.webdriver.webelement import WebElement
from appium.webdriver.client_config import AppiumClientConfig

from selenium.common import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

from utils.finder import by_converter
from utils.decorators import resolve_wait_method
from core.modules import AppPlatform
from core.settings import IMPLICIT_WAIT_TIMEOUT, EXPLICIT_WAIT_TIMEOUT, APPIUM_HOST, APPIUM_PORT

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CoreDriver:
    def __init__(self):
        """
        初始化 CoreDriver 实例。
        从 settings.py 加载默认的 Appium 服务器主机和端口。
        """
        self.driver: Optional[webdriver.Remote] = None
        self._host = APPIUM_HOST
        self._port = APPIUM_PORT

    def server_config(self, host: str = APPIUM_HOST, port: int = APPIUM_PORT):
        self._host = host
        self._port = port
        logger.info(f"Appium Server 指向 -> {self._host}:{self._port}")
        return self

    def connect(self, platform: str | AppPlatform, caps: dict,
                extensions: list[Type[ExtensionBase]] | None = None,
                client_config: AppiumClientConfig | None = None) -> 'CoreDriver':
        """
        连接到 Appium 服务器并创建一个新的会话。

        :param platform: 目标平台 ('android' 或 'ios')，支持 AppPlatform 枚举或字符串。
        :param caps: Appium capabilities 字典。
        :param extensions: Appium 驱动扩展列表。
        :param client_config: Appium 客户端配置。
        :return: 返回 CoreDriver 实例自身，支持链式调用。
        :raises ValueError: 如果平台不受支持。
        :raises ConnectionError: 如果无法连接到 Appium 服务。
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
    def find_element(self, by, value, timeout: Optional[float] = None) -> WebElement:
        """
        内部通用查找（显式等待）
        :param by: 定位策略
        :param value: 定位值
        :param timeout: 等待超时时间 (秒)。如果为 None, 则使用全局默认超时.
        :return: WebElement.
        """
        by = by_converter(by)
        mark = (by, value)
        wait_timeout = timeout if timeout is not None else EXPLICIT_WAIT_TIMEOUT
        return WebDriverWait(self.driver, wait_timeout).until(EC.presence_of_element_located(mark))

    def delay(self, timeout: int | float) -> 'CoreDriver':
        """
        强制等待（线程阻塞）。

        应谨慎使用，主要用于等待非 UI 元素的异步操作或调试。
        :param timeout: 等待时间（秒）。
        :return: self
        """
        sleep(timeout)
        return self

    def implicit_wait(self, timeout: float = IMPLICIT_WAIT_TIMEOUT) -> None:
        """
        设置全局隐式等待时间。
        在每次 find_element 时生效，直到元素出现或超时。
        :param timeout: 超时时间
        :return:
        """
        self.driver.implicitly_wait(timeout)

    @resolve_wait_method
    def explicit_wait(self, method: Union[Callable[[webdriver.Remote], T], str], timeout: Optional[float] = None) -> \
            Union[T, WebElement]:
        """
        执行显式等待，直到满足某个条件或超时。
        :param method: EC等待条件(Callable) 或 自定义等待条件的名称(str)
        :param timeout: 超时时间 (秒)。如果为 None, 则使用全局默认超时.
        :return: 等待条件的执行结果 (通常是 WebElement 或 bool)
        """
        wait_timeout = timeout if timeout is not None else EXPLICIT_WAIT_TIMEOUT

        try:
            # 获取函数名称用于日志，兼容 lambda 和普通函数
            func_name = getattr(method, '__name__', repr(method))
            logger.info(f"执行显式等待: {func_name}, 超时: {wait_timeout}s")
            return WebDriverWait(self.driver, wait_timeout).until(method)
        except TypeError as te:
            logger.error(f"显示等待异常: {te}")
            # self.driver.quit()
            raise te

    def page_load_timeout(self, timeout: Optional[float] = None) -> None:
        """
        设置页面加载超时时间。
        :param timeout: 超时时间 (秒)。如果为 None, 则使用全局默认超时.
        """
        wait_timeout = timeout if timeout is not None else EXPLICIT_WAIT_TIMEOUT
        self.driver.set_page_load_timeout(wait_timeout)

    def click(self, by, value, timeout: Optional[float] = None) -> 'CoreDriver':
        """
        查找元素并执行点击操作。
        内置显式等待，确保元素可点击。
        :param by: 定位策略。
        :param value: 定位值。
        :param timeout: 等待超时时间。
        :return: self
        """
        by = by_converter(by)
        mark = (by, value)
        logger.info(f"点击: {mark}")
        method = EC.element_to_be_clickable(mark)
        self.explicit_wait(method, timeout).click()
        return self

    def clear(self, by, value, timeout: Optional[float] = None) -> 'CoreDriver':
        """
        查找元素并清空其内容。
        内置显式等待，确保元素可见。
        :param by: 定位策略。
        :param value: 定位值。
        :param timeout: 等待超时时间。
        :return: self
        """
        by = by_converter(by)
        mark = (by, value)
        logger.info(f"清空输入框: {mark}")
        method = EC.visibility_of_element_located(mark)
        self.explicit_wait(method, timeout).clear()
        return self

    def input(self, by, value, text, timeout: Optional[float] = None) -> 'CoreDriver':
        """
        查找元素并输入文本。
        内置显式等待，确保元素可见。
        :param by: 定位策略。
        :param value: 定位值。
        :param text: 要输入的文本。
        :param timeout: 等待超时时间。
        :return: self
        """
        by = by_converter(by)
        mark = (by, value)
        logger.info(f"输入文本到 {mark}: '{text}'")
        method = EC.visibility_of_element_located(mark)
        self.explicit_wait(method, timeout).send_keys(text)
        return self

    def is_visible(self, by: str, value: str, timeout: Optional[float] = None) -> bool:
        """
        判断元素是否可见
        :param by: 定位策略。
        :param value: 定位值。
        :param timeout: 等待超时时间。
        :return: bool
        """
        try:
            by = by_converter(by)
            mark = (by, value)
            method = EC.visibility_of_element_located(mark)
            self.explicit_wait(method, timeout)
            return True
        except TimeoutException:
            return False

    def get_text(self, by, value, timeout: Optional[float] = None) -> str:
        """
        获取元素文本
        :param by: 定位策略。
        :param value: 定位值。
        :param timeout: 等待超时时间。
        :return:获取到的文本
        """
        by = by_converter(by)
        mark = (by, value)
        method = EC.visibility_of_element_located(mark)

        text = self.explicit_wait(method, timeout).text
        logger.info(f"获取到的文本{text}")
        return text

    @property
    def session_id(self):
        """获取当前 Appium 会话的 Session ID。"""
        return self.driver.session_id

    # --- 移动端特有：方向滑动 ---
    def swipe_by_coordinates(self, start_x: int, start_y: int, end_x: int, end_y: int,
                             duration: int = 1000) -> 'CoreDriver':
        """
        基于绝对坐标的滑动 (W3C Actions 底层实现)
        :param start_x: 起点 X
        :param start_y: 起点 Y
        :param end_x: 终点 X
        :param end_y: 终点 Y
        :param duration: 滑动持续时间 (ms)
        :return: self
        """
        actions = ActionChains(self.driver)
        # 覆盖默认的鼠标输入为触摸输入
        actions.w3c_actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))

        actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(duration / 1000)
        actions.w3c_actions.pointer_action.move_to_location(end_x, end_y)
        actions.w3c_actions.pointer_action.release()
        actions.perform()
        return self

    def swipe(self, direction: str = "up", duration: int = 1000) -> 'CoreDriver':
        """
        封装方向滑动
        :param direction: 滑动方向 up/down/left/right
        :param duration: 滑动持续时间 (ms)
        :return: self
        """
        # 每次获取屏幕尺寸以适应旋转
        size = self.driver.get_window_size()
        w, h = size['width'], size['height']

        # 定义滑动坐标 (中心区域，避开边缘，防止误触系统操作)
        coords = {
            "up": (w * 0.5, h * 0.8, w * 0.5, h * 0.2),
            "down": (w * 0.5, h * 0.2, w * 0.5, h * 0.8),
            "left": (w * 0.9, h * 0.5, w * 0.1, h * 0.5),
            "right": (w * 0.1, h * 0.5, w * 0.9, h * 0.5)
        }
        start_x, start_y, end_x, end_y = coords.get(direction.lower(), coords["up"])
        logger.info(f"执行滑动: {direction} ({start_x}, {start_y}) -> ({end_x}, {end_y})")

        return self.swipe_by_coordinates(start_x, start_y, end_x, end_y, duration)

    def long_press(self, element: Optional[WebElement] = None, x: Optional[int] = None, y: Optional[int] = None,
                   duration: int = 2000) -> 'CoreDriver':
        """
        长按封装：支持传入元素或坐标
        """
        if element:
            rect = element.rect
            x = rect['x'] + rect['width'] // 2
            y = rect['y'] + rect['height'] // 2

        if x is None or y is None:
            raise ValueError("Long press requires an element or (x, y) coordinates.")

        # 复用 swipe_by_coordinates，当起点和终点一致时，即为长按效果。
        # 逻辑：Move -> Down -> Pause -> Move(原地) -> Release
        return self.swipe_by_coordinates(x, y, x, y, duration)

    def drag_and_drop(self, source_el: WebElement, target_el: WebElement, duration: int = 1000) -> 'CoreDriver':
        """
        将 source_el 拖拽到 target_el
        """
        s_rect = source_el.rect
        t_rect = target_el.rect

        sx, sy = s_rect['x'] + s_rect['width'] // 2, s_rect['y'] + s_rect['height'] // 2
        tx, ty = t_rect['x'] + t_rect['width'] // 2, t_rect['y'] + t_rect['height'] // 2

        logger.info(f"执行拖拽: ({sx}, {sy}) -> ({tx}, {ty})")
        return self.swipe_by_coordinates(sx, sy, tx, ty, duration)

    def smart_scroll(self, element: WebElement, direction: str = "down") -> 'CoreDriver':
        """
        智能滚动：自动识别平台并调用最稳定的原生滚动脚本
        :param element: 需要滚动的容器元素 (如 ScrollView, RecyclerView, TableView)
        :param direction: 滚动方向 'up', 'down', 'left', 'right'
        """
        platform = self.driver.capabilities.get('platformName', '').lower()
        match platform:
            case AppPlatform.ANDROID.value:
                # Android UiAutomator2 专用滚动手势
                self.driver.execute_script('mobile: scrollGesture', {
                    'elementId': element.id,
                    'direction': direction,
                    'percent': 1.0
                })
            case AppPlatform.IOS.value:
                # iOS XCUITest 专用滚动 (默认为 iOS 处理)
                self.driver.execute_script("mobile: scroll", {
                    "elementId": element.id,
                    "direction": direction
                })

        return self

    def swipe_by_percent(self, start_xp, start_yp, end_xp, end_yp, duration: int = 1000) -> 'CoreDriver':
        """
        按屏幕比例滑动 (0.5 = 50%)
        """
        size = self.driver.get_window_size()
        w, h = size['width'], size['height']

        return self.swipe_by_coordinates(
            int(w * start_xp),
            int(h * start_yp),
            int(w * end_xp),
            int(h * end_yp),
            duration
        )

    @property
    def is_alive(self) -> bool:
        """判断当前驱动会话是否仍然存活。"""
        return self.driver is not None and self.driver.session_id is not None

    # --- 断言逻辑 ---
    def assert_text(self, by, value, expected_text, timeout: Optional[float] = None) -> 'CoreDriver':
        """
        断言元素的文本内容是否符合预期。
        :param by: 定位策略。
        :param value: 定位值。
        :param expected_text: 期望的文本。
        :param timeout: 等待元素可见的超时时间。
        :return: self，支持链式调用。
        :raises AssertionError: 如果文本不匹配。
        """
        actual = self.get_text(by, value, timeout)
        assert actual == expected_text, f"断言失败: 期望 {expected_text}, 实际 {actual}"
        logger.info(f"断言通过: 文本匹配 '{actual}'")
        return self

    def quit(self):
        """安全关闭 Appium 驱动并断开连接。"""
        if self.driver:
            try:
                # 获取 session_id 用于日志追踪
                sid = self.session_id
                self.driver.quit()
                logger.info(f"已安全断开连接 (Session: {sid})")
            except Exception as e:
                logger.warning(f"断开连接时发生异常 (可能服务已预先关闭): {e}")
            finally:
                self.driver = None
        else:
            logger.debug("没有正在运行的 Driver 实例需要关闭。")
