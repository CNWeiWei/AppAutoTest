#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: logger
@date: 2026/1/15 11:30
@desc: 
"""
import time
import functools
import inspect
import logging

from core.settings import LOG_DIR

# 1. 确定日志存储路径
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


# --- 核心特性：装饰器集成 ---
def trace_step(step_desc="", source='wrapper'):
    """
    通用执行追踪装饰器：
    1. 智能识别并过滤 self/cls 参数
    2. 记录入参、出参、耗时
    3. 异常自动捕获并记录
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取对应的 logger
            _logger = logging.getLogger(source)
            # _logger = logging.getLogger(f"{source}.{func.__name__}")

            # 参数解析 (跳过 self/cls)
            sig = inspect.signature(func)
            params = list(sig.parameters.values())
            display_args = args[1:] if params and params[0].name in ('self', 'cls') else args

            # 格式化参数显示，方便阅读
            args_repr = [repr(a) for a in display_args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            all_params = ", ".join(args_repr + kwargs_repr)

            func_name = f"{func.__module__}.{func.__name__}"

            _logger.info(f"[步骤开始] | {step_desc} | 方法: {func_name}({all_params})")

            start_t = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_t
                _logger.info(f"[步骤成功] {step_desc} | 耗时: {duration:.2f}s | 返回: {result!r}")
                return result
            except Exception as e:
                duration = time.perf_counter() - start_t
                # logging.exception 关键点：它会自动把详细的堆栈信息写入日志文件
                _logger.error(f"[步骤失败] {step_desc}| 耗时: {duration:.2f}s|异常: {type(e).__name__}")
                # f"[步骤失败] {step_desc} | 耗时: {duration:.2f}s | 异常: {type(e).__name__}: {e}")
                raise e

        return wrapper

    return decorator
