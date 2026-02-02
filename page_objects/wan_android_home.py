#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: test_home
@date: 2026/1/30 17:18
@desc: 
"""
import logging

import allure
from appium import webdriver

from core.base_page import BasePage

logger = logging.getLogger(__name__)


class HomePage(BasePage):
    # 定位参数
    text = ("accessibility id", "Text")
    unicode = ("accessibility id", "Unicode")

    def __init__(self, driver: webdriver.Remote):
        super().__init__(driver)

    @allure.step("点击 “Text ”")
    def click_text(self):
        if self.wait_until_visible(*self.text, timeout=1):
            with allure.step("发现Text，开始执行点击"):
                # self.log_screenshot_bytes("Text截图").click(*self.text)
                self.log_screenshot_bytes("Text截图")
                self.click(*self.text)

    @allure.step("点击 “Unicode ”：{1}")
    def click_unicode(self, taget):
        """执行登录业务逻辑"""
        # 调用继承自 CoreDriver 的方法（假设你的 CoreDriver 已经被注入或组合）

        if self.wait_until_visible(*self.unicode):
            self.swipe("left")

        self.click(*self.unicode).log_screenshot()

    @allure.step("获取 “Text ”文本")
    def get_home_text(self):
        """执行登录业务逻辑"""
        # 调用继承自 CoreDriver 的方法（假设你的 CoreDriver 已经被注入或组合）

        return self.get_text(*self.text)
