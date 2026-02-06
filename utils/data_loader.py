#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: data_loader
@date: 2026/1/27 10:00
@desc: 数据加载工具
"""
import yaml
from pathlib import Path
from typing import Any, List


def load_yaml(file_path: Path | str) -> dict[str, Any] | List[Any]:
    """
    加载 YAML 文件
    :param file_path: 文件路径
    :return: 数据字典或列表
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
