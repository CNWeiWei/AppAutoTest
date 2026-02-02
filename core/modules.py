#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: modules
@date: 2026/1/20 11:54
@desc: 
"""

from enum import Enum

class AppPlatform(Enum):
    """
    定义支持的移动应用平台枚举。
    """
    ANDROID = "android"
    IOS = "ios"


class Locator(str, Enum):
    """
    定义元素定位策略枚举。
    继承 str 以便直接作为参数传递给 Selenium/Appium 方法。
    """
    # --- 原有 Selenium 支持 ---
    ID = "id"
    NAME = "name"
    CLASS = "class"
    TAG = "tag"
    LINK_TEXT = "link_text"
    PARTIAL_LINK_TEXT = "partial_link_text"
    CSS = "css"
    XPATH = "xpath"
    # --- Appium 特有支持 ---
    ACCESSIBILITY_ID = "accessibility_id"
    AID = "aid"  # 简写
    ANDROID_UIAUTOMATOR = "android_uiautomator"
    IOS_PREDICATE = "ios_predicate"