#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: test_views
@date: 2026/1/30 17:37
@desc: 
"""
import logging

import allure
from appium import webdriver

from core.base_page import BasePage

logger = logging.getLogger(__name__)


class ViewsPage(BasePage):
    # 定位参数
    views = ("accessibility id","Views")

    def __init__(self, driver: webdriver.Remote):
        super().__init__(driver)

    @allure.step("截图 “Views ”")
    def screenshot_views(self):
        if self.wait_until_visible(*self.views):
            with allure.step("发现Views，开始执行点击"):
                self.log_screenshot_bytes("Text截图")
