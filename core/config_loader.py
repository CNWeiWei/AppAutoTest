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
import logging
from typing import Any, Optional
from utils.data_loader import load_yaml
from core.settings import CAPS_CONFIG_PATH, ENV_CONFIG, CURRENT_ENV

logger = logging.getLogger(__name__)


def get_env_config(env_name: Optional[str] = None) -> dict[str, str]:
    """
    获取当前运行环境的业务配置信息。

    逻辑：
    1. 优先使用传入的 `env_name`。
    2. 若未传入，使用全局设置 `CURRENT_ENV`。
    3. 若都为空，默认为 "test"。
    4. 如果目标环境在配置中不存在，强制回退到 "test" 环境并记录警告。

    :param env_name: 指定的环境名称 (e.g., "dev", "prod")，可选。
    :return: 对应环境的配置字典。
    """
    target_env = env_name or CURRENT_ENV or "test"

    if target_env not in ENV_CONFIG:
        logger.warning(f"环境 '{target_env}' 未在配置中定义，将回退到 'test' 环境。")
        return ENV_CONFIG.get("test", {})

    return ENV_CONFIG[target_env]


def get_caps(caps_name: str) -> dict[str, Any]:
    """
    从 YAML 配置文件加载指定的 Appium Capabilities。

    :param caps_name: 配置文件中的设备/平台名称 (不区分大小写)，例如 "android_pixel"。
    :return: 该设备对应的 Capabilities 字典。
    :raises ValueError: 当指定的 caps_name 在配置文件中不存在时。
    :raises RuntimeError: 当配置文件加载失败或格式错误时。
    """
    try:
        all_caps = load_yaml(CAPS_CONFIG_PATH)
        all_caps = {k.lower(): v for k, v in all_caps.items()}
        caps_key = caps_name.lower()

        if caps_key not in all_caps:
            raise ValueError(f"在 {CAPS_CONFIG_PATH} 中找不到平台 '{caps_key}' 的配置")

        return all_caps[caps_key]

    except Exception as e:
        raise RuntimeError(f"加载 Capabilities 失败 ({CAPS_CONFIG_PATH}): {e}")
