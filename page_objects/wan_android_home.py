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
    menu = ("accessibility id", "开启")
    home = ("id", 'com.manu.wanandroid:id/largeLabel')
    project = ("-android uiautomator", 'new UiSelector().text("项目")')
    system = ("-android uiautomator", 'new UiSelector().text("体系")')

    tv_name = ("id", "com.manu.wanandroid:id/tvName")

    account=("-android uiautomator",'new UiSelector().text("账号")')
    pass_word=("-android uiautomator",'new UiSelector().text("密码")')

    login_button = ("accessibility id", '登录')

    def __init__(self, driver: webdriver.Remote):
        super().__init__(driver)

    @allure.step("点击 “侧边栏”")
    def click_open(self):
        if self.wait_until_visible(*self.menu, timeout=1):
            self.click(*self.menu)
            self.attach_screenshot_bytes("侧边栏截图")
        with allure.step("准备登录"):
            self.click(*self.tv_name)

    @allure.step("登录账号：{1}")
    def login(self, username, password):
        """执行登录业务逻辑"""
        account_element_id =self.find_element(*self.account).id
        account_input = {"elementId": account_element_id, "text": username}

        pwd_element_id =self.find_element(*self.pass_word).id
        pass_word_input = {"elementId": pwd_element_id, "text": password}

        if self.wait_until_visible(*self.login_button):
            self.click(*self.account).driver.execute_script('mobile: type', account_input)
            self.click(*self.pass_word).driver.execute_script('mobile: type', pass_word_input)

        self.click(*self.login_button)

        if self.wait_until_visible(*self.tv_name):
            self.full_screen_screenshot("登陆成功")
            self.long_press(x=636,y=117,duration=300)

