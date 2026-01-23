#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: test
@date: 2026/1/14 10:12
@desc: 
"""

# import pytest
from enum import Enum
from typing import TypeVar
from utils.logger import logger, trace_step


# --- 模拟业务逻辑 ---

class ServiceRole(Enum):
    MANAGED = "受控模式"
    EXTERNAL = "共享模式"
    NULL = "无效模式"


class AppiumService:
    def __init__(self, device_id: str, role: ServiceRole):
        self.device_id = device_id
        self.role = role
        # 使用 bind 为该实例的所有日志绑定特定的设备 ID
        self._log = logger.bind(source=f"Dev:{device_id}")

    @trace_step(step_desc="停止服务", source="Appium")
    def stop(self, force=False):
        """演示类方法追踪及逻辑分支"""
        self._log.info(f"正在尝试停止服务，强制模式={force}")

        if self.role == ServiceRole.EXTERNAL:
            self._log.warning("外部服务，跳过清理进程")
            return "SKIPPED"

        if self.role == ServiceRole.MANAGED:
            self._log.success("已发送 SIGTERM 信号清理进程")
            return "SUCCESS"

        raise RuntimeError("无法停止处于未知状态的服务")

    @trace_step("简单打印")
    def simple_log(self, msg: str):
        self._log.info(f"消息回显: {msg}")


# --- 独立函数演示 ---

@trace_step("执行数据计算", source="Calc")
def calculate_data(a: int, b: int):
    if b == 0:
        raise ZeroDivisionError("除数不能为 0")
    return a / b


@trace_step("空值返回测试")
def return_none():
    return None


# --- 测试场景覆盖 ---

def run_scenarios():
    print("\n" + "=" * 50)
    print("🚀 开始执行全场景日志覆盖测试")
    print("=" * 50 + "\n")

    # 1. 覆盖：正常类方法调用 (过滤 self)
    logger.info(">>> 场景 1: 正常类方法 (MANAGED 模式)")
    svc1 = AppiumService("emulator-5554", ServiceRole.MANAGED)
    svc1.stop(force=True)

    # 2. 覆盖：类方法不同返回值
    logger.info(">>> 场景 2: 共享模式跳过清理")
    svc2 = AppiumService("iPhone_15", ServiceRole.EXTERNAL)
    svc2.stop()

    # 3. 覆盖：异常捕获 (自动记录错误日志并向上抛出)
    logger.info(">>> 场景 3: 异常捕获测试")
    try:
        calculate_data(10, 0)
    except ZeroDivisionError:
        logger.warning("主流程已捕获预期的计算异常")

    # 4. 覆盖：复杂参数与 None 返回
    logger.info(">>> 场景 4: 复杂参数与 None 返回")
    return_none()

    # 5. 覆盖：未定义状态导致的崩溃
    logger.info(">>> 场景 5: 业务逻辑崩溃测试")
    svc3 = AppiumService("Unknown_Device", ServiceRole.NULL)
    try:
        svc3.stop()
    except Exception as e:
        logger.error(f"捕获到业务逻辑崩溃:{e}")

    # 6. 覆盖：原生 logger 与装饰器 logger 混合
    logger.info(">>> 场景 6: 验证自定义 source 标签")
    # 这里会使用 setup_logger 中定义的默认 'System' 标签
    logger.debug("这是一条调试级别的原始日志")

    print("\n" + "=" * 50)
    print("✅ 测试场景执行完毕，请检查 logs 文件夹中的 .log 文件")
    print("=" * 50)


if __name__ == "__main__":
    run_scenarios()