#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: config_loader
@date: 2026/1/16 10:52
@desc: Pytest 核心配置与 Fixture 管理
"""

from typing import Any
from utils.data_loader import load_yaml
from core.settings import CAPS_CONFIG_PATH, ENV_CONFIG, CURRENT_ENV
from core.modules import AppPlatform


def get_env_config() -> dict[str, str]:
    """
    根据当前环境 (CURRENT_ENV) 获取对应的业务配置
    """
    return ENV_CONFIG.get(CURRENT_ENV, ENV_CONFIG["test"])


def get_caps(platform: str) -> dict[str, Any]:
    """
    从 YAML 文件加载 Capabilities 配置
    """
    try:
        all_caps = load_yaml(CAPS_CONFIG_PATH)
        all_caps = {k.lower(): v for k, v in all_caps.items()}
        platform_key = platform.lower()

        if platform_key not in all_caps:

            base_caps: dict[str, Any] = {
                "noReset": False,
                "newCommandTimeout": 60,
            }

            match platform_key:
                case AppPlatform.ANDROID:
                    android_caps = {
                        "platformName": "Android",
                        "automationName": "uiautomator2",
                        "deviceName": "Android",
                        "appPackage": "com.manu.wanandroid",
                        "appActivity": "com.manu.wanandroid.ui.main.activity.MainActivity",
                    }
                    return base_caps | android_caps
                case AppPlatform.IOS:

                    ios_caps = {
                        "platformName": "iOS",
                        "automationName": "XCUITest",
                        "deviceName": "iPhone 14",
                        "bundleId": "com.example.app",
                        "autoAcceptAlerts": True,
                        "waitForQuiescence": False,
                    }
                    return base_caps | ios_caps

        return all_caps[platform_key]

    except Exception as e:
        raise RuntimeError(f"无法加载“caps”内容 {CAPS_CONFIG_PATH}: {e}")
