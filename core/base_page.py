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
from typing import Type, TypeVar, List, Tuple

from appium import webdriver
from selenium.common import TimeoutException

from core.driver import CoreDriver

# 定义一个泛型，用于类型推断（IDE 依然会有补全提示）
T = TypeVar('T', bound='BasePage')
logger = logging.getLogger(__name__)


class BasePage(CoreDriver):

    def __init__(self, driver: webdriver.Remote):
        super().__init__(driver)
        # 定义常见弹窗的关闭按钮定位

    # 这里放全局通用的 Page 属性和逻辑

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
