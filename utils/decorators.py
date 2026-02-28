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
    一个结合了上下文管理器和装饰器功能的追踪器。

    主要职责是记录一个代码块或函数的执行情况，包括：
    - 开始和结束的日志，并根据上下文进行缩进，形成层级结构。
    - 计算并记录执行耗时。
    - 捕获并记录执行期间发生的异常。

    可作为上下文管理器使用:
    with StepTracer("处理数据"):
        ...

    也可作为装饰器的一部分（通过 step_trace 工厂函数）。
    """

    def __init__(self, step_desc, source='wrapper', func_info=None):
        """
        初始化 StepTracer。
        :param step_desc: 对当前步骤或操作的描述。
        :param source: 日志记录器的名称。
        :param func_info: 关联的函数信息，用于日志输出。
        """
        self.step_desc = step_desc
        self.logger = logging.getLogger(source)
        self.func_info = func_info
        self.start_t = None

    def __enter__(self):
        """
        进入上下文，记录步骤开始，并增加日志缩进层级。
        """
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
        """
        退出上下文，记录步骤结束（成功或失败）、耗时，并恢复日志缩进层级。
        如果发生异常，会记录异常信息但不会抑制它，异常会继续向上传播。
        """
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
    装饰器：将字符串形式的等待条件解析为可调用的 Expected Condition (EC) 对象。

    这个装饰器用于修饰那些接受一个 `method` 参数的方法（通常是等待方法）。
    如果 `method` 是一个字符串，它会尝试将其解析为一个预定义的 `expected_conditions`。

    字符串格式支持:
    - "key": 直接映射到一个无参数的 EC。
    - "key:arg1,arg2": 映射到一个需要参数的 EC，参数以逗号分隔。

    解析逻辑委托给 `core.custom_expected_conditions.get_condition` 函数。
    如果解析失败，会记录错误并重新抛出异常。

    Args:
        func (Callable): 被装饰的函数。

    Returns:
        Callable: 包装后的函数。
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
    装饰器：在被装饰方法成功执行后，自动触发截图。

    主要用于UI自动化测试中，记录关键业务操作执行后的页面状态。
    它会调用被装饰对象（通常是 Page Object）的 `attach_screenshot_bytes` 方法。

    注意:
    - 截图操作在原方法成功返回后执行。
    - 被装饰的实例 (`self`) 必须拥有 `attach_screenshot_bytes` 方法。
    - 如果截图失败，会记录一个警告日志，但不会影响主流程。

    Args:
        func (Callable): 被装饰的函数。

    Returns:
        Callable: 包装后的函数。
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
    """
    辅助函数：格式化函数调用的参数，以便清晰地记录日志。

    它会检查函数的签名，并执行以下操作：
    1. 过滤掉实例方法或类方法中的 `self` 或 `cls` 参数。
    2. 将位置参数和关键字参数格式化为一个可读的字符串。

    Args:
        func (Callable): 目标函数。
        *args: 传递给函数的位置参数。
        **kwargs: 传递给函数的关键字参数。

    Returns:
        str: 格式化后的参数字符串，例如 "arg1, kwarg='value'"。
    """
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
    装饰器工厂：创建一个通用的执行追踪装饰器。

    此装饰器利用 `StepTracer` 上下文管理器来提供结构化的日志，记录
    函数的调用、参数、执行耗时和任何发生的异常。

    功能包括:
    - 自动格式化并记录函数的输入参数（会智能过滤 `self` 和 `cls`）。
    - 使用 `StepTracer` 生成带缩进的层级式日志，清晰展示调用栈。
    - 记录每个被追踪步骤的开始、成功/失败状态以及执行耗时。
    - 捕获并记录异常，但不会抑制异常，保证上层逻辑可以处理。

    用法:
        @step_trace("执行用户登录操作")
        def login(username, password):
            ...

    Args:
        step_desc (str, optional): 对被装饰函数所执行操作的描述。
                                   如果为空，日志中将只显示函数信息。
        source (str, optional): 指定日志记录器的名称。默认为 'wrapper'。

    Returns:
        Callable: 一个可以装饰函数的装饰器。
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
