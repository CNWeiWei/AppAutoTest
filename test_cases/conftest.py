#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: conftest
@date: 2026/1/19 14:08
@desc: 
"""
import pytest
import allure
from pathlib import Path


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    本钩子函数会在每个测试阶段（setup, call, teardown）执行后被调用。
    item: 测试用例对象
    call: 测试执行阶段的信息
    """
    # 1. 先执行常规的用例报告生成逻辑
    outcome = yield
    report = outcome.get_result()

    # 2. 我们只关注测试执行阶段 ("call")
    # 如果该阶段失败了（failed），则触发截图
    if report.when == "call" and report.failed:
        # 3. 从测试用例中获取 driver 实例
        # 假设你在 fixture 中注入的参数名为 'driver'
        driver_instance = item.funcargs.get("driver")

        if driver_instance:
            try:
                # 4. 调用你在 CoreDriver 中实现的底层截图方法
                # 这里的 name 我们可以动态取测试用例的名字
                case_name = item.name
                file_path = driver_instance.full_screen_screenshot(name=f"CRASH_{case_name}")

                # 5. 如果路径存在，将其关联到 Allure 报告
                if file_path:
                    p = Path(file_path)
                    if p.exists():
                        allure.attach.file(
                            source=p,
                            name="【故障现场自动截图】",
                            attachment_type=allure.attachment_type.PNG
                        )
            except Exception as e:
                print(f"故障自动截图执行失败: {e}")