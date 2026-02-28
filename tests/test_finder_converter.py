#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: test_finder_converter
@date: 2026/1/20 15:40
@desc: 测试 utils/finder.py 中的 FinderConverter 逻辑
"""

import pytest
from appium.webdriver.common.appiumby import AppiumBy
from utils.finder import by_converter, register_custom_finder, converter


class TestFinderConverter:

    def setup_method(self):
        """每个测试用例开始前重置 converter 状态"""
        converter.clear_custom_finders()

    def teardown_method(self):
        """每个测试用例结束后重置 converter 状态"""
        converter.clear_custom_finders()

    @pytest.mark.parametrize("input_by, expected", [
        ("id", "id"),
        ("xpath", "xpath"),
        ("link text", "link text"),
        ("aid", AppiumBy.ACCESSIBILITY_ID),
        ("class", AppiumBy.CLASS_NAME),
        ("css", AppiumBy.CSS_SELECTOR),
        ("uiautomator", AppiumBy.ANDROID_UIAUTOMATOR),
        ("predicate", AppiumBy.IOS_PREDICATE),
        ("chain", AppiumBy.IOS_CLASS_CHAIN),
    ])
    def test_standard_and_shortcuts(self, input_by, expected):
        """测试标准定位方式和简写"""
        assert by_converter(input_by) == expected

    @pytest.mark.parametrize("input_by, expected", [
        ("ID", "id"),
        (" Id ", "id"),
        ("accessibility_id", AppiumBy.ACCESSIBILITY_ID),
        ("accessibility-id", AppiumBy.ACCESSIBILITY_ID),
        ("-ios class chain", AppiumBy.IOS_CLASS_CHAIN),
        (" -Ios-Class-Chain ", AppiumBy.IOS_CLASS_CHAIN),
        ("UI_AUTOMATOR", AppiumBy.ANDROID_UIAUTOMATOR),
    ])
    def test_normalization(self, input_by, expected):
        """测试归一化容错 (大小写、空格、下划线、横杠)"""
        assert by_converter(input_by) == expected

    def test_custom_registration(self):
        """测试自定义注册功能"""
        register_custom_finder("my_text", "-android uiautomator")
        assert by_converter("my_text") == "-android uiautomator"

        # 测试注册后归一化依然生效
        assert by_converter("MY_TEXT") == "-android uiautomator"

    def test_reset_functionality(self):
        """测试重置功能"""
        register_custom_finder("temp_key", "xpath")
        assert by_converter("temp_key") == "xpath"

        converter.clear_custom_finders()

        with pytest.raises(ValueError, match="Unsupported locator strategy"):
            by_converter("temp_key")

    def test_invalid_strategy(self):
        """测试不支持的定位策略"""
        with pytest.raises(ValueError, match="Unsupported locator strategy"):
            by_converter("unknown_strategy")

    def test_invalid_types(self):
        """测试非法类型输入"""
        with pytest.raises(ValueError, match="Invalid selector type"):
            by_converter(123)  # type: ignore

        with pytest.raises(ValueError, match="Invalid selector type"):
            by_converter(None)  # type: ignore


if __name__ == "__main__":
    pytest.main(["-v", __file__])
