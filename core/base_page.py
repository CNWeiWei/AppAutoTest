#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: base_page
@date: 2026/1/26 17:33
@desc: 
"""
import logging
import secrets
from typing import Type, TypeVar, List, Tuple, Optional
import allure
from pathlib import Path
from appium import webdriver
from selenium.common import TimeoutException

from core.driver import CoreDriver
from utils.decorators import exception_capture

# 定义一个泛型，用于类型推断（IDE 依然会有补全提示）
T = TypeVar('T', bound='BasePage')
logger = logging.getLogger(__name__)


class BasePage(CoreDriver):

    def __init__(self, driver: webdriver.Remote):
        super().__init__(driver)
        # 定义常见弹窗的关闭按钮定位

    def log_screenshot(self, label: str = "步骤截图"):
        """
        业务级截图：执行截图并附加到 Allure 报告。
        用户可自由手动调用此方法。
        """
        path_str = self.full_screen_screenshot(name=label)

        if path_str:
            img_path = Path(path_str)
            if img_path.exists():
                allure.attach.file(
                    img_path,
                    name=label,
                    attachment_type=allure.attachment_type.PNG
                )

    def log_screenshot_bytes(self, label: str = "步骤截图"):
        """
        业务级截图：执行截图并附加到 Allure 报告。
        用户可自由手动调用此方法。
        """
        _img: bytes = self.driver.get_screenshot_as_png()

        allure.attach(
            _img,
            name=label,
            attachment_type=allure.attachment_type.PNG
        )

    # --- 常用断言逻辑 ---
    def assert_text(self, by: str, value: str, expected_text: str, timeout: Optional[float] = None) -> 'BasePage':
        """
        断言元素的文本内容是否符合预期。
        :param by: 定位策略。
        :param value: 定位值。
        :param expected_text: 期望的文本。
        :param timeout: 等待元素可见的超时时间。
        :return: self，支持链式调用。
        :raises AssertionError: 如果文本不匹配。
        """
        # 1. 增强报告展示：将断言动作包装为一个清晰的步骤
        step_name = f"断言校验 | 预期结果: '{expected_text}'"
        with allure.step(step_name):
            actual = self.get_text(by, value, timeout)
            # 2. 动态附件：在报告中直观对比，方便后期排查
            allure.attach(
                f"预期值: {expected_text}\n实际值: {actual}",
                name="文本对比结果",
                attachment_type=allure.attachment_type.TEXT
            )
            # 3. 执行核心断言
            # 如果断言失败，抛出的 AssertionError 会被 conftest.py 中的 Hook 捕获并截图
            assert actual == expected_text, f"断言失败: 期望 {expected_text}, 实际 {actual}"
            logger.info(f"断言通过: 文本匹配 '{actual}'")
        return self

    # 这里放全局通用的 Page 属性和逻辑
    def assert_visible(self, by: str, value: str, msg: str = "元素可见性校验"):
        """
        增强版断言：成功/失败均截图
        """
        with allure.step(f"断言检查: {msg}"):
            try:
                element = self.find_element(by, value)
                assert element.is_displayed()
                # 成功存证
            except Exception as e:
                raise e

    # 封装一些所有页面通用的元动作
    def clear_permission_popups(self):
        # 普适性黑名单
        _black_list = [
            ("id", "com.android.packageinstaller:id/permission_allow_button"),
            ("xpath", "//*[@text='始终允许']"),
            ("xpath", "//*[@text='稍后提醒']"),
            ("xpath", "//*[@text='以后再说']"),
            ("id", "com.app:id/iv_close_global_ad"),
            ("accessibility id", "Close"),  # iOS 常用
        ]
        self.clear_popups(_black_list)

    def clear_business_ads(self):
        """在这里定义一些全 App 通用的业务广告清理"""
        _ads = [("id", "com.app:id/global_ad_close")]
        return self.clear_popups(_ads)

    def get_toast(self, text):
        return self.is_visible("text", text)

    def go_to(self, page_name: Type[T]) -> T:
        """
        通用的页面跳转/获取方法
        :param page_name: 目标页面类
        :return: 目标页面的实例
        """
        logger.info(f"跳转到页面: {page_name.__name__}")
        return page_name(self.driver)
