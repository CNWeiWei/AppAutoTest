#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: enums
@date: 2026/2/27 17:05
@desc: 
"""
from enum import Enum


class AppiumStatus(Enum):
    """Appium 服务状态枚举"""
    READY = "服务已启动"  # 服务和驱动都加载完成 (HTTP 200 + ready: true)
    INITIALIZING = "驱动正在加载"  # 服务已响应但驱动仍在加载 (HTTP 200 + ready: false)
    CONFLICT = "端口被其他程序占用"  # 端口被其他非 Appium 程序占用
    OFFLINE = "服务未启动"  # 服务未启动
    ERROR = "内部错误"
    UNKNOWN = "未知状态"


class ServiceRole(Enum):
    """服务角色枚举：定义服务的所有权和生命周期"""
    MANAGED = "托管模式"  # 由本脚本启动，负责清理
    EXTERNAL = "共享模式"  # 复用现有服务，不负责清理
    NULL = "空模式"  # 无效或未初始化的服务


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
