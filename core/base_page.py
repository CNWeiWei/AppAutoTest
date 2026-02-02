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
from pathlib import Path
from typing import Type, TypeVar, Optional

import allure
from appium import webdriver

from core.driver import CoreDriver

# 定义一个泛型，用于类型推断
T = TypeVar('T', bound='BasePage')

logger = logging.getLogger(__name__)


class BasePage(CoreDriver):
    # --- 全局通用的属性 ---
    def __init__(self, driver: webdriver.Remote):
        """
        初始化 BasePage。

        :param driver: Appium WebDriver 实例
        """
        super().__init__(driver)

    # --- 所有页面通用的元动作 ---
    def go_to(self, page_cls: Type[T]) -> T:
        """
        通用的页面跳转/实例化方法 (Page Factory)。

        :param page_cls: 目标页面类 (BasePage 的子类)
        :return: 目标页面的实例
        """
        logger.info(f"跳转到页面: {page_cls.__name__}")
        return page_cls(self.driver)

    def handle_permission_popups(self):
        """
        处理通用的系统权限弹窗。
        遍历预定义的黑名单，尝试关闭出现的系统级弹窗（如权限申请、安装确认等）。
        """
        # 普适性黑名单
        popup_blacklist = [
            ("id", "com.android.packageinstaller:id/permission_allow_button"),
            ("xpath", "//*[@text='始终允许']"),
            ("xpath", "//*[@text='稍后提醒']"),
            ("xpath", "//*[@text='以后再说']"),
            ("id", "com.app:id/iv_close_global_ad"),
            ("accessibility id", "Close"),  # iOS 常用
        ]
        self.clear_popups(popup_blacklist)

    def handle_business_ads(self):
        """
        处理全 App 通用的业务广告弹窗。
        针对应用启动后可能出现的全局广告进行关闭处理。
        """
        ads_blacklist = [("id", "com.app:id/global_ad_close")]
        return self.clear_popups(ads_blacklist)

    def save_and_attach_screenshot(self, label: str = "日志截图") -> None:
        """
        保存截图到本地并附加到 Allure 报告。
        
        :param label: 截图在报告中显示的名称
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

    def attach_screenshot_bytes(self, label: str = "日志截图") -> None:
        """
        直接获取内存中的截图数据并附加到 Allure 报告（不存本地文件）。
        
        :param label: 截图在报告中显示的名称
        """
        screenshot_bytes: bytes = self.driver.get_screenshot_as_png()

        allure.attach(
            screenshot_bytes,
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

    def assert_visible(self, by: str, value: str, msg: str = "元素可见性校验") -> 'BasePage':
        """
        断言元素是否可见。
        
        :param by: 定位策略
        :param value: 定位值
        :param msg: 断言描述信息
        :return: self，支持链式调用
        """
        with allure.step(f"断言检查: {msg}"):
            element = self.find_element(by, value)
            is_displayed = element.is_displayed()

            if is_displayed:
                logger.info(f"断言通过: 元素 [{value}] 可见")

            assert is_displayed, f"断言失败: 元素 [{value}] 不可见"
        return self
