#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: test_settings
@date: 2026/1/16 15:56
@desc: 
"""
import logging

from utils.logger import trace_step

logger = logging.getLogger(__name__)

@trace_step("验证失败",)
def test_settings_page_display(driver):
    """
    测试设置页面是否成功加载
    """
    # 此时 driver 已经通过 fixture 完成了初始化
    current_act = driver.driver.current_activity
    logger.info(f"捕获到当前 Activity: {current_act}")

    assert ".unihome.UniHomeLauncher" in current_act


def test_wifi_entry_exists(driver):
    """
    简单的元素查找示例
    """
    # 这里的 driver 就是 appium.webdriver.Remote 实例
    # 假设我们要查找“网络”相关的 ID
    # el = driver.find_element(by='id', value='android:id/title')
    assert driver.driver.session_id is not None