#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: home_page
@date: 2026/1/26 17:37
@desc: 
"""

from core.base_page import BasePage
class HomePage(BasePage):
    _LOGOUT_BTN = ("text", "退出登录")
    _NICKNAME = ("id", "user_nickname")

    def get_nickname(self):
        return self.driver.get_text(*self._NICKNAME)

    def logout(self):
        self.driver.click(*self._LOGOUT_BTN)
        # 【核心：链式跳转】
        # 退出后回到登录页
        return self.login_page