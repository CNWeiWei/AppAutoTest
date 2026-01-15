#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com,chenwei@zygj.com
@file: logger
@date: 2026/1/15 11:30
@desc: 
"""
import sys
import time
import functools
from pathlib import Path
import inspect
from loguru import logger

# 1. 确定日志存储路径
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 2. 统一定义日志格式 (美化版)
# <green> 等标签是控制台颜色，文件日志中会自动剥离颜色代码
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<magenta>{extra[source]: <8}</magenta> | "
    "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def setup_logger():
    """
    只需在项目入口调用一次。
    如果是简单的自动化脚本，甚至可以直接在模块内执行。
    """
    # 移除 Loguru 默认的控制台处理器（避免重复打印）
    logger.remove()

    # 添加自定义控制台输出
    logger.add(
        sys.stdout,
        format=LOG_FORMAT,
        level="INFO",
        colorize=True,
        # 默认给一个 'Global' 的 device 标签
        filter=lambda record: record["extra"].setdefault("source", "System")
    )

    # 添加按天滚动的日志文件
    logger.add(
        str(LOG_DIR / "appium_{time:YYYY-MM-DD}.log"),
        format=LOG_FORMAT,
        level="DEBUG",
        rotation="00:00",  # 每天午夜滚动
        retention="10 days",  # 保留最近10天
        compression="zip",  # 旧日志自动压缩
        encoding="utf-8",
        enqueue=True  # 开启队列模式，确保多线程下日志不串行
    )


# --- 核心特性 1：装饰器集成 ---
def trace_step(step_desc="", source: str = 'task'):
    """
    通用执行追踪装饰器：
    1. 智能识别并过滤 self/cls 参数
    2. 记录入参、出参、耗时
    3. 异常自动捕获并记录
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # --- 智能参数解析 ---
            # 获取函数的签名
            sig = inspect.signature(func)
            params = list(sig.parameters.values())

            # 检查第一个参数名是否为 'self' 或 'cls'
            # 这样既兼容了 PageObject 的实例方法，也兼容了纯函数
            if params and params[0].name in ('self', 'cls'):
                display_args = args[1:]
            else:
                display_args = args

            # 格式化参数显示，方便阅读
            args_repr = [repr(a) for a in display_args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            all_params = ", ".join(args_repr + kwargs_repr)

            func_name = f"{func.__module__}.{func.__name__}"

            # 使用 bind 临时改变这一步的 source 标签

            _logger = logger.bind(source=source)
            # 使用关联的上下文 logger
            # logger.info(f"🚀 [步骤开始] {step_desc} | 执行方法: {func_name} | 参数: {display_args} {kwargs}")
            _logger.info(f"🚀 [步骤开始] {step_desc} | 方法: {func_name}({all_params})")

            start_t = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_t
                _logger.success(f"✅ [步骤成功] {step_desc} | 耗时: {duration:.2f}s | 返回: {result!r}")
                return result
            except Exception as e:
                duration = time.perf_counter() - start_t
                _logger.error(
                    f"❌ [步骤失败] {step_desc} | 耗时: {duration:.2f}s | 异常: {type(e).__name__}: {e}")
                raise e

        return wrapper

    return decorator


# 初始化
setup_logger()

# 导出供外部使用
__all__ = ["logger", "trace_step"]
