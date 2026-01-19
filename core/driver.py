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
from typing import Optional, Type

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from appium.options.common.base import AppiumOptions
from appium.webdriver.webdriver import ExtensionBase
from appium.webdriver.client_config import AppiumClientConfig


logger = logging.getLogger(__name__)

class AppPlatform(Enum):
    ANDROID = "android"
    IOS = "ios"


class AppDriver:
    def __init__(self):
        self.driver: Optional[webdriver.Remote] = None
        self._host = "127.0.0.1"
        self._port = 4723

    def server_config(self):
        """配置服务端信息"""
        # self._host = host
        # self._port = port
        logger.info(f"Appium Server 指向 -> {self._host}:{self._port}")

    def connect(self, platform: str | AppPlatform, caps: dict,
                extensions: list[Type[ExtensionBase]] | None = None,
                client_config: AppiumClientConfig | None = None) -> 'AppDriver':
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

    # --- 开始封装操作方法 ---
    def click(self, locator: tuple):
        """封装点击，locator 格式如 (AppiumBy.ID, "xxx")"""
        logger.info(f"点击元素: {locator}")
        self.driver.find_element(*locator).click()

    def input(self, locator: tuple, text: str):
        """封装输入"""
        logger.info(f"对元素 {locator} 输入内容: {text}")
        el = self.driver.find_element(*locator)
        el.clear()
        el.send_keys(text)



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
