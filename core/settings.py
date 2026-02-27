#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: settings
@date: 2026/1/19 16:54
@desc: 全局配置管理
"""

import os
from pathlib import Path

# 项目根目录 (core 的上一级)
BASE_DIR = Path(__file__).resolve().parents[1]

# --- 目录配置 ---
OUTPUT_DIR = BASE_DIR / "outputs"
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
LOG_DIR = OUTPUT_DIR / "logs"
LOG_BACKUP_DIR = LOG_DIR / "backups"
ALLURE_TEMP = BASE_DIR / "temp"
REPORT_DIR = BASE_DIR / "reports"
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"

# 需要初始化的目录列表
REQUIRED_DIRS = [LOG_DIR, LOG_BACKUP_DIR, ALLURE_TEMP, SCREENSHOT_DIR]

# --- 文件路径 ---
LOG_SOURCE = LOG_DIR / "pytest.log"
CAPS_CONFIG_PATH = CONFIG_DIR / "caps.yaml"

# --- 启动 Appium 最大尝试次数 ---
MAX_RETRIES = 40

# --- 核心配置 ---
IMPLICIT_WAIT_TIMEOUT = 10
EXPLICIT_WAIT_TIMEOUT = 10

# 默认 Appium Server 地址 (可通过命令行参数覆盖)
APPIUM_HOST = "127.0.0.1"
APPIUM_PORT = 4723

# --- 环境配置 (Environment Switch) ---
CURRENT_ENV = os.getenv("APP_ENV", "test")

# base_url：业务接口的入口地址。主要用于通过 API 快速构造测试数据（前置条件）或查询数据库/接口状态来验证 App 操作是否生效（数据断言）
# source_address：后端服务器的物理/源站地址。通常用于绕过负载均衡或 DNS 直接指定访问特定的服务器节点。
ENV_CONFIG = {
    "test": {
        "base_url": "https://test.example.com",
        "source_address": "192.168.1.100"
    },
    "uat": {
        "base_url": "https://uat.example.com",
        "source_address": "192.168.1.200"
    },
    "prod": {
        "base_url": "https://www.example.com",
        "source_address": "10.0.0.1"
    }
}
