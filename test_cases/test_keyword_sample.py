#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: test_keyword_sample
@date: 2026/1/23 17:48
@desc: 
"""

import pytest
import logging
from core.driver import CoreDriver
from utils.data_loader import DataLoader
from core.settings import BASE_DIR

logger = logging.getLogger(__name__)

# 假设数据文件路径
DATA_FILE = BASE_DIR / "test_cases" / "data" / "login_flow.xlsx"


# 或者 "login_flow.yaml" —— 代码不需要改动，只需要改文件名

class TestKeywordDriven:

    def run_step(self, driver: CoreDriver, step: dict):
        """
        核心执行引擎：反射调用 CoreDriver 的方法
        """
        action_name = step.get("action")
        if not action_name:
            return  # 跳过无效行

        # 1. 获取 CoreDriver 中对应的方法
        if not hasattr(driver, action_name):
            raise ValueError(f"CoreDriver 中未定义方法: {action_name}")

        func = getattr(driver, action_name)

        # 2. 准备参数
        # 你的 CoreDriver 方法签名通常是 (by, value, [args], timeout)
        # 我们从 step 字典中提取这些参数
        kwargs = {}
        if "by" in step and step["by"]: kwargs["by"] = step["by"]
        if "value" in step and step["value"]: kwargs["value"] = step["value"]

        # 处理特殊参数，比如 input 方法需要的 text，或者 assert_text 需要的 expected_text
        # 这里做一个简单的映射，或者在 Excel 表头直接写对应参数名
        if "args" in step and step["args"]:
            # 假设 input 的第三个参数是 text，这里简单处理，实际可根据 func.__code__.co_varnames 动态匹配
            if action_name == "input":
                kwargs["text"] = str(step["args"])  # 确保 Excel 数字转字符串
            elif action_name == "assert_text":
                kwargs["expected_text"] = str(step["args"])
            elif action_name == "explicit_wait":
                # 支持你封装的 resolve_wait_method
                # 此时 method 参数就是 args 列的内容，例如 "toast_visible:成功"
                kwargs["method"] = step["args"]

        logger.info(f"执行步骤 [{step.get('desc', '无描述')}]: {action_name} {kwargs}")

        # 3. 执行调用
        func(**kwargs)

    def test_execute_from_file(self, driver):
        """
        主测试入口
        """
        # 1. 加载数据 (自动识别 Excel/YAML)
        # 注意：实际使用时建议把 load 放在 pytest.mark.parametrize 里
        # 这里为了演示逻辑写在函数内
        if not DATA_FILE.exists():
            pytest.skip("数据文件不存在")

        steps = DataLoader.load(DATA_FILE)

        # 2. 遍历执行
        for step in steps:
            self.run_step(driver, step)
