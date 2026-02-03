#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: decorators
@date: 2026/1/15 11:30
@desc:
"""

import logging
import time
import inspect
from functools import wraps
from typing import Union, Callable

from contextvars import ContextVar
from contextlib import ContextDecorator

from core.custom_expected_conditions import get_condition

logger = logging.getLogger(__name__)

# 定义一个上下文变量，初始值为 0
indent_var = ContextVar("indent_level", default=0)


class StepTracer(ContextDecorator):
    """
    既是装饰器也是上下文管理器
    职责：负责计时、日志格式化和异常记录
    """

    def __init__(self, step_desc, source='wrapper', func_info=None):
        self.step_desc = step_desc
        self.logger = logging.getLogger(source)
        self.func_info = func_info
        self.start_t = None

    def __enter__(self):
        # 1. 获取当前层级并计算前缀
        level = indent_var.get()
        # 使用 "  " (空格) 或 "│ " 作为缩进符号
        self.prefix = "│  " * level

        self.start_t = time.perf_counter()
        info = f" | 方法: {self.func_info}" if self.func_info else ""
        # self.logger.info(f"[步骤开始] | {self.step_desc}{info}")
        self.logger.info(f"{self.prefix}┌── [步骤开始] | {self.step_desc}{info}")

        # 2. 进入下一层，层级 +1
        indent_var.set(level + 1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 3. 恢复层级，层级 -1
        level = indent_var.get() - 1
        indent_var.set(level)

        duration = time.perf_counter() - self.start_t

        prefix = "│  " * level

        if exc_type:
            # 异常发生
            # self.logger.error(
            #     f"[步骤失败] {self.step_desc} | 耗时: {duration:.2f}s | 异常: {exc_type.__name__}"
            # )
            self.logger.error(
                f"{prefix}└── [步骤失败] {self.step_desc} | 耗时: {duration:.2f}s | 异常: {exc_type.__name__}"
            )
        else:
            # 执行成功
            # self.logger.info(f"[步骤成功] {self.step_desc} | 耗时: {duration:.2f}s")
            self.logger.info(
                f"{prefix}└── [步骤成功] {self.step_desc} | 耗时: {duration:.2f}s"
            )
        # return False 确保异常继续向上抛出，不拦截异常
        return False


def resolve_wait_method(func):
    """
    装饰器：将字符串形式的等待条件解析为可调用的 EC 对象
    """

    @wraps(func)
    def wrapper(self, method: Union[Callable, str], *args, **kwargs):
        if isinstance(method, str):
            # 解析格式 "key:arg1,arg2" 或 仅 "key"
            ec_name = method
            ec_args = []

            if ":" in method:
                ec_name, params = method.split(":", 1)
                if params:
                    ec_args = params.split(",")

            # 委托给 core.custom_expected_conditions.get_condition 处理
            try:
                logger.info(f"解析命名等待条件: '{ec_name}' 参数: {ec_args}")
                method = get_condition(ec_name, *ec_args)
            except Exception as e:
                logger.error(f"解析等待条件 '{method}' 失败: {e}")
                raise e

        return func(self, method, *args, **kwargs)

    return wrapper


def action_screenshot(func):
    """
    显式截图装饰器：在方法执行前（或后）立即触发 BasePage 的截图逻辑。
    用于记录关键操作后的页面状态。
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # 1. 正常执行原方法
        result = func(self, *args, **kwargs)

        # 2. 执行成功后立即截图（如果你希望在操作后的状态截图）
        if hasattr(self, "attach_screenshot_bytes"):
            try:
                class_name = self.__class__.__name__
                func_name = func.__name__
                msg = f"操作记录_{class_name}_{func_name}"
                # 传入当前方法名作为截图备注
                self.attach_screenshot_bytes(msg)
            except Exception as e:
                logger.warning(f"装饰器执行截图失败: {e}")

        return result

    return wrapper


def _format_params(func, *args, **kwargs):
    """辅助函数：专门处理参数过滤和格式化"""
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    display_args = args[1:] if params and params[0].name in ('self', 'cls') else args

    # 格式化参数显示，方便阅读
    args_repr = [repr(a) for a in display_args]
    kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
    all_params = ", ".join(args_repr + kwargs_repr)
    return all_params


def step_trace(step_desc="", source='wrapper'):
    """
    通用执行追踪装饰器：
    1. 智能识别并过滤 self/cls 参数
    2. 记录入参、出参、耗时
    3. 异常自动捕获并记录
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 1. 提取参数显示逻辑 (抽离出来可以作为工具函数)
            all_params = _format_params(func, *args, **kwargs)
            func_name = f"{func.__module__}.{func.__name__}"

            # 2. 使用上下文管理器
            with StepTracer(step_desc, source, f"{func_name}({all_params})"):
                return func(*args, **kwargs)

        return wrapper

    return decorator
