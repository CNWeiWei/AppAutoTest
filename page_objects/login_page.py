#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: login_page
@date: 2026/1/26 17:34
@desc: 
"""

from core.base_page import BasePage
from page_objects.home_page import HomePage

class LoginPage(BasePage):
    # 定位参数私有化，不暴露给外面
    _USER_FIELD = ("id", "com.app:id/username")
    _PWD_FIELD = ("id", "com.app:id/password")
    _LOGIN_BTN = ("id", "com.app:id/btn_login")

    def login_as(self, username, password):
        """执行登录业务逻辑"""
        # 调用继承自 CoreDriver 的方法（假设你的 CoreDriver 已经被注入或组合）
        self.driver.input(*self._USER_FIELD, text=username)
        self.driver.input(*self._PWD_FIELD, text=password, sensitive=True)
        self.driver.click(*self._LOGIN_BTN)

        # 【核心：链式跳转】
        # 登录成功后，逻辑上应该进入首页，所以返回首页实例
        return self.to_page(HomePage)