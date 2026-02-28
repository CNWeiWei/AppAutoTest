#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: wan_android_project
@date: 2026/1/30 17:37
@desc: 
"""
import logging

import allure
from appium import webdriver

from core.base_page import BasePage
from utils.decorators import StepTracer

logger = logging.getLogger(__name__)


class ProjectPage(BasePage):
    # 定位参数
    project_title = ("-android uiautomator", 'new UiSelector().text("项目")')
    pro_table_title = ("-android uiautomator", 'new UiSelector().text("完整项目")')

    def __init__(self, driver: webdriver.Remote):
        super().__init__(driver)

    @allure.step("切换到“项目”页面")
    def switch_to_project(self):
        self.click(*self.project_title).attach_screenshot_bytes()

    @allure.step("滑动切换“项目”内容")
    @StepTracer("页面滑动")
    def slide_views(self):
        with allure.step("向左滑动3次"):
            with StepTracer("开始划了"):
                for _ in range(3):
                    self.swipe("left")
