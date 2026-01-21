#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com,chenwei@zygj.com
@file: locator_utils
@date: 2026/1/20 15:40
@desc: 
"""
from typing import Literal, Final
from appium.webdriver.common.appiumby import AppiumBy

ByType = Literal[
    # By(selenium)
    "id", "xpath", "link text", "partial link text", "name", "tag name", "class name", "css selector",
        # AppiumBy
    '-ios predicate string',
    '-ios class chain',
    '-android uiautomator',
    '-android viewtag',
    '-android datamatcher',
    '-android viewmatcher',
    'accessibility id',
    '-image',
    '-custom',
    '-flutter semantics label',
    '-flutter type',
    '-flutter key',
    '-flutter text',
    '-flutter text containing',
        # 自定义常用简写 (Shortcuts)
    "aid", "class", "css", "uiautomator", "predicate", "chain",
]

class FinderConverter:
    """
    定位查找转换工具类
    提供策略的归一化处理、简写映射及动态自定义注册
    """

    # 预设的常用简写
    _BUILTIN_SHORTCUTS: Final = {
        "aid": AppiumBy.ACCESSIBILITY_ID,
        "class": AppiumBy.CLASS_NAME,
        "css": AppiumBy.CSS_SELECTOR,
        "uiautomator": AppiumBy.ANDROID_UIAUTOMATOR,
        "predicate": AppiumBy.IOS_PREDICATE,
        "chain": AppiumBy.IOS_CLASS_CHAIN,
    }

    def __init__(self):
        self._finder_map: dict[str, str] = {}
        self._map_cache: dict[str, str] = {}
        self._initialize()

    @staticmethod
    def _normalize(text: str) -> str:
        """
        统一清洗逻辑：转小写、去除空格、下划线、横杠
        """
        if not isinstance(text, str):
            raise TypeError(f"Locator strategy must be a string, got {type(text).__name__} instead.")
        return text.lower().strip().replace('_', '').replace(' ', '').replace('-', '')

    def _initialize(self) -> None:
        """初始化基础映射表"""
        # 1. 动态加载 AppiumBy 常量值
        for attr_name in dir(AppiumBy):
            if attr_name.startswith("_"):
                continue

            attr_value = getattr(AppiumBy, attr_name)
            if isinstance(attr_value, str):
                # "class name" -> classname,"class_name" -> classname
                self._finder_map[self._normalize(attr_value)] = attr_value

        # 2. 加载内置简写（会覆盖同名的策略）
        self._finder_map.update(self._BUILTIN_SHORTCUTS)

        # 3. 备份初始状态
        self._map_cache = self._finder_map.copy()

    def convert(self, by_value: ByType | str) -> str:
        """
        将模糊或简写的定位方式转换为 Appium 标准定位字符串
        :raises ValueError: 当定位方式不支持时抛出
        """
        if not by_value or not isinstance(by_value, str):
            raise ValueError(f"Invalid selector type: {type(by_value)}. Expected a string.")

        clean_key = self._normalize(by_value)
        target = self._finder_map.get(clean_key)

        if target is None:
            raise ValueError(f"Unsupported locator strategy: '{by_value}'.")
        return target

    def register_custom_finder(self, alias: str, target: str) -> None:
        """注册自定义定位策略"""
        self._finder_map[self._normalize(alias)] = target

    def clear_custom_finders(self) -> None:
        """重置回初始官方/内置状态"""
        self._finder_map = self._map_cache.copy()

    def get_all_finders(self) -> list[str]:
        """返回当前所有支持的策略 key（用于调试）"""
        return list(self._finder_map.keys())


# 导出单例，方便直接使用
converter = FinderConverter()
by_converter = converter.convert
register_custom_finder = converter.register_custom_finder

__all__=["by_converter", "register_custom_finder"]

if __name__ == '__main__':
    # 1. 测试标准转换与内置简写
    print(f"ID 转换: {by_converter('id')}")                  # 输出: id
    print(f"AID 简写转换: {by_converter('aid')}")           # 输出: accessibility id
    print(f"CSS 简写转换: {by_converter('css')}")           # 输出: css selector

    # 2. 测试强大的归一化容错 (空格、下划线、横杠、大小写)
    print(f"类链容错: {by_converter(' -Ios-Class-Chain ')}") # 输出: -ios class chain
    print(f"UIAutomator 容错: {by_converter('UI_AUTOMATOR')}") # 输出: -android uiautomator

    # 3. 测试自定义注册
    register_custom_finder("my_text", "-android uiautomator")
    print(f"自定义注册测试: {by_converter('my_text')}")      # 输出: -android uiautomator

    # 4. 测试重置功能
    converter.clear_custom_finders()
    print("已重置自定义查找器")
    try:
        by_converter("my_text")
    except ValueError as e:
        print(f"验证重置成功 (捕获异常): {e}")

    # 5. 查看当前全量支持的归一化后的 Key
    print(f"当前支持的策略总数: {len(converter.get_all_finders())}")
    print(f"前 5 个策略示例: {converter.get_all_finders()[:5]}")
    # 6. 增加类型非法测试
    print("\n--- 异常类型测试 ---")
    try:
        by_converter(123)  # 传入数字
    except TypeError as e:
        print(f"验证类型拦截成功: {e}")

    try:
        by_converter(None) # 传入 None
    except TypeError as e:
        print(f"验证空值拦截成功: {e}")