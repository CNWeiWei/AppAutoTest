#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: settings
@date: 2026/1/19 16:54
@desc: 
"""
import os
# core/settings.py
from pathlib import Path

# 项目根目录 (core 的上一级)
# BASE_DIR = Path(__file__).parent.parent
BASE_DIR = Path(__file__).resolve().parents[1]  # 获取根路径（绝对路径）
# print(BASE_DIR)
# --- 目录配置 ---
OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = OUTPUT_DIR / "logs"
LOG_BACKUP_DIR = LOG_DIR / "backups"
ALLURE_TEMP = BASE_DIR / "temp"
REPORT_DIR = BASE_DIR / "report"
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
# 确保必要的目录存在
for folder in [LOG_DIR, LOG_BACKUP_DIR, ALLURE_TEMP, SCREENSHOT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# --- 文件路径 ---
LOG_SOURCE = LOG_DIR / "pytest.log"

# --- 启动 Appium 最大尝试次数 ---
MAX_RETRIES = 40
# --- 业务常量 (可选) ---
IMPLICIT_WAIT_TIMEOUT = 10
EXPLICIT_WAIT_TIMEOUT = 10
APPIUM_SERVER = "http://127.0.0.1:4723"
# --- 核心配置 ---
APPIUM_HOST = "127.0.0.1"
APPIUM_PORT = 4723

# --- 设备能力配置 (Capabilities) ---
ANDROID_CAPS = {
    "platformName": "Android",
    "automationName": "uiautomator2",
    "deviceName": "Android",
    "appPackage": "com.android.settings",
    "appActivity": ".Settings",
    "noReset": False
}
# ANDROID_CAPS = {
#     "platformName": "Android",
#     "automationName": "uiautomator2",
#     "deviceName": "Android",
#     "appPackage": "com.bocionline.ibmp",
#     "appActivity": "com.bocionline.ibmp.app.main.launcher.LauncherActivity",
#     "noReset":False
# }
IOS_CAPS = {
    "platformName": "iOS",
    "automationName": "XCUITest",
    "autoAcceptAlerts": True,  # 自动接受系统权限请求
    "waitForQuiescence": False,  # 设为 False 可加速扫描
    # 如果是某些特定的业务弹窗 autoAcceptAlerts 无效，
    # 此时就会触发我们代码里的 PopupManager.solve()
}
