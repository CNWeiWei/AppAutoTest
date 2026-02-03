#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: path_manager
@date: 2026/2/3 10:52
@desc: 
"""

from pathlib import Path

from core.settings import REQUIRED_DIRS


def ensure_dirs_ok():
    """
    统一管理项目目录的创建逻辑
    """
    for folder in REQUIRED_DIRS:
        # 使用 exist_ok=True 避免并发冲突
        folder.mkdir(parents=True, exist_ok=True)


def ensure_dir(path: Path) -> Path:
    """确保路径存在并返回路径本身"""
    if not isinstance(path, Path):
        path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
