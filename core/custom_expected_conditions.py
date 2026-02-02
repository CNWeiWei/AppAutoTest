#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: custom_expected_conditions
@date: 2026/1/22 16:13
@desc: 自定义预期条件 (Expected Conditions)
用于 WebDriverWait 的显式等待判断逻辑。
"""

import logging
from typing import Any, Union

from appium.webdriver.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException

logger = logging.getLogger(__name__)

"""
    常用等待条件（expected_conditions）--来自EC模块
        presence_of_element_located: 元素存在于DOM。
        visibility_of_element_located: 元素可见。
        element_to_be_clickable: 元素可点击。
        title_contains: 页面标题包含特定文本。
        text_to_be_present_in_element: 元素包含特定文本。
"""


# 自定义预期条件(Custom Expected Condition)
class BaseCondition:
    """
    基础条件类：负责统一的 WebDriverWait 协议实现和异常拦截。
    所有自定义的类形式 EC 都应继承此类
    """

    def __call__(self, driver: WebDriver):
        """
        WebDriverWait 调用的入口方法。
        
        :param driver: WebDriver 实例
        :return: check 方法的返回值，或者在捕获异常时返回 False
        """
        try:
            return self.check(driver)
        except (NoSuchElementException, StaleElementReferenceException):
            return False

    def check(self, driver: WebDriver):
        """
        执行具体的检查逻辑，由子类实现。

        :param driver: WebDriver 实例
        :return: 判定成功返回对象或 True，失败返回 False
        """
        raise NotImplementedError("子类必须实现 check 方法")


EC_MAPPING: dict[str, Any] = {}


def register(name: str = None):
    """
    自定义预期条件注册装饰器：
    1. @register() -> 使用函数名注册
    2. @register("alias") -> 使用别名注册
    3. register("name", func) -> 手动注入

    :param name: 注册别名，默认为函数/类名
    :return: 装饰器函数
    """

    def decorator(item):
        reg_name = name or item.__name__
        EC_MAPPING[reg_name] = item
        return item

    return decorator


@register("toast_visible")
class ToastVisible(BaseCondition):
    """检查 Toast 消息是否可见"""

    def __init__(self, text: str, partial: Union[str, bool] = True):
        """
        :param text: 期望的 Toast 文本
        :param partial: 是否部分匹配 (默认 True)
        """
        self.text = text
        # 处理从装饰器传来的字符串 "true"/"false"
        if isinstance(partial, str):
            self.partial = partial.lower() != "false"
        else:
            self.partial = partial

    def check(self, driver: WebDriver):
        # 注意：这里不再需要显式 try-except，BaseCondition 会处理
        xpath = f"//*[contains(@text, '{self.text}')]" if self.partial else f"//*[@text='{self.text}']"
        element = driver.find_element(By.XPATH, xpath)
        return element if element.is_displayed() else False


@register("attr_contains")
class ElementHasAttribute(BaseCondition):
    """检查元素的属性是否包含特定值"""

    # 扁平化参数以支持字符串调用: "attr_contains:id,btn_id,checked,true"
    def __init__(self, by: str, value: str, attribute: str, expect_value: str):
        """
        :param by: 定位策略
        :param value: 定位值
        :param attribute: 属性名
        :param expect_value: 期望包含的属性值
        """
        self.locator = (by, value)
        self.attribute = attribute
        self.value = expect_value

    def check(self, driver: WebDriver):
        element = driver.find_element(*self.locator)
        attr_value = element.get_attribute(self.attribute)
        return element if (attr_value and self.value in attr_value) else False


@register()
class ElementCountAtLeast(BaseCondition):
    """检查页面上匹配定位符的元素数量是否至少为 N 个"""

    def __init__(self, by: str, value: str, count: Union[str, int]):
        self.locator = (by, value)
        # 确保字符串参数转为整数
        self.count = int(count)

    def check(self, driver: WebDriver) -> bool | list[WebElement]:
        elements = driver.find_elements(*self.locator)
        if len(elements) >= self.count:
            return elements
        return False


@register()  # 使用函数名 is_element_present 注册
def is_element_present(by: str, value: str):
    """
    检查元素是否存在于 DOM 中 (不一定可见)。

    :param by: 定位策略
    :param value: 定位值
    :return: 判定函数
    """
    locator = (by, value)

    def _predicate(driver):
        try:
            return driver.find_element(*locator)
        except Exception as e:
            logger.warning(f"{__name__}异常：{e}")
            return False

    return _predicate


@register()
def system_ready(api_client):
    """
    检查外部系统 (API) 是否就绪。

    :param api_client: API 客户端实例
    :return: 判定函数
    """

    def _predicate(_):  # 忽略传入的 driver

        try:
            return api_client.get_status() == "OK"
        except Exception as e:
            logger.warning(f"{__name__}异常：{e}")
            return False

    return _predicate


def get_condition(method: Union[str, Any], *args, **kwargs):
    """
    智能获取预期条件：
    1. 如果 method 是字符串，先查自定义 EC_MAPPING
    2. 如果自定义里没有，去官方 selenium.webdriver.support.expected_conditions 找
    3. 如果 method 本身就是 Callable (比如 EC.presence_of_element_located)，直接透传

    :param method: 预期条件名称 (str) 或 可调用对象
    :param args: 传递给条件的参数
    :param kwargs: 传递给条件的关键字参数
    :return: 实例化后的预期条件对象 (Callable)
    """

    # 情况 A: 如果传入的是官方 EC 对象或自定义函数实例，直接返回
    if callable(method) and not isinstance(method, type):
        return method

    # 情况 B: 如果传入的是字符串别名
    if isinstance(method, str):
        # 1. 尝试从自定义映射查找
        if method in EC_MAPPING:
            target = EC_MAPPING[method]
        # 2. 尝试从官方 EC 库查找
        elif hasattr(EC, method):
            target = getattr(EC, method)
        else:
            raise ValueError(f"找不到预期条件: {method}. 请检查拼写或是否已注册。")

        # 实例化并返回 (无论是类还是闭包工厂)
        return target(*args, **kwargs)

    # 情况 C: 传入的是类名本身
    if isinstance(method, type):
        return method(*args, **kwargs)

    raise TypeError(f"不支持的条件类型: {type(method)}")


if __name__ == "__main__":
    # print(EC_MAPPING)
    cond1 = get_condition("toast_visible", "保存成功")
    print(cond1)
    # 调用闭包生成的条件
    # cond2 = get_condition("is_element_present", (By.ID, "submit"))
    # print(cond2)
    cond3 = get_condition(EC.presence_of_element_located, (By.ID, "submit"))
    print(cond3)
    cond4 = get_condition("system_ready", (By.ID, "submit"))
    print(cond4)
    # WebDriverWait(driver, 10).until(cond1)
