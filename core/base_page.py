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
from typing import Type, TypeVar
from core.driver import CoreDriver
# 定义一个泛型，用于类型推断（IDE 依然会有补全提示）
T = TypeVar('T', bound='BasePage')
logger = logging.getLogger(__name__)
class BasePage:
    def __init__(self, driver: CoreDriver):
        self.driver = driver
    # 这里放全局通用的 Page 属性和逻辑
    # --- 页面工厂：属性懒加载 ---
    # 这样你可以在任何页面直接通过 self.home_page 访问首页
    @property
    def home_page(self):
        from page_objects.home_page import HomePage
        return HomePage(self.driver)

    @property
    def login_page(self):
        from page_objects.login_page import LoginPage
        return LoginPage(self.driver)

    # 封装一些所有页面通用的元动作
    def get_toast(self, text):
        return self.driver.is_visible("text", text)

    def to_page(self, page_class: Type[T]) -> T:
        """
        通用的页面跳转/获取方法
        :param page_class: 目标页面类
        :return: 目标页面的实例
        """
        logger.info(f"跳转到页面: {page_class.__name__}")
        return page_class(self.driver)