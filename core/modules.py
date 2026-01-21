#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com,chenwei@zygj.com
@file: modules
@date: 2026/1/20 11:54
@desc: 
"""

from enum import Enum

class Locator(str, Enum):
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