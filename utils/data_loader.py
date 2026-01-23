#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: data_loader.py
@date: 2026/1/23 13:55
@desc: 
"""
# !/usr/bin/env python
# coding=utf-8

"""
@author: CNWei
@desc: 数据驱动加载器 (Adapter Pattern 实现)
       负责将 YAML, JSON, Excel 统一转换为 Python List[Dict] 格式
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Union

import yaml

# 尝试导入 openpyxl，如果未安装则在运行时报错提示
try:
    import openpyxl
except ImportError:
    openpyxl = None

logger = logging.getLogger(__name__)


class DataLoader:
    """
    数据加载适配器
    统一输出格式: List[Dict]
    """

    @staticmethod
    def load(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        入口方法：根据文件后缀分发处理逻辑
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"测试数据文件未找到: {path}")

        suffix = path.suffix.lower()

        logger.info(f"正在加载测试数据: {path.name}")

        if suffix in ['.yaml', '.yml']:
            return DataLoader._load_yaml(path)
        elif suffix == '.json':
            return DataLoader._load_json(path)
        elif suffix in ['.xlsx', '.xls']:
            return DataLoader._load_excel(path)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}。仅支持 yaml, json, xlsx")

    @staticmethod
    def _load_yaml(path: Path) -> List[Dict]:
        with open(path, 'r', encoding='utf-8') as f:
            # safe_load 防止代码注入风险
            data = yaml.safe_load(f)
            # 归一化：如果根节点是字典，转为单元素列表；如果是列表则直接返回
            return data if isinstance(data, list) else [data]

    @staticmethod
    def _load_json(path: Path) -> List[Dict]:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]

    @staticmethod
    def _load_excel(path: Path) -> List[Dict]:
        """
        Excel 解析规则：
        1. 第一行默认为表头 (Keys)
        2. 后续行为数据 (Values)
        3. 自动过滤全空行
        """
        if openpyxl is None:
            raise ImportError("检测到 .xlsx 文件，但未安装 openpyxl。请执行: pip install openpyxl")

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        # 默认读取第一个 Sheet
        ws = wb.active

        # 获取所有行
        rows = list(ws.rows)
        if not rows:
            return []

        # 解析表头 (第一行)
        headers = [cell.value for cell in rows[0] if cell.value is not None]

        result = []
        # 解析数据 (从第二行开始)
        for row in rows[1:]:
            # 提取当前行的数据
            values = [cell.value for cell in row]

            # 如果整行都是 None，跳过
            if not any(values):
                continue

            # 组装字典: {header: value}
            row_dict = {}
            for i, header in enumerate(headers):
                # 防止越界 (有些行可能数据列数少于表头)
                val = values[i] if i < len(values) else None
                # 转换处理：Excel 的数字可能需要转为字符串，视业务需求而定
                # 这里保持原样，由后续逻辑处理类型
                row_dict[header] = val

            result.append(row_dict)

        wb.close()
        return result


if __name__ == "__main__":
    # 调试代码
    # 假设有一个 test.yaml
    # print(DataLoader.load("test.yaml"))
    pass