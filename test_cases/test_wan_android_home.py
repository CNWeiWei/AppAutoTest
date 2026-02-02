#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: test_api_demos
@date: 2026/1/30 17:42
@desc: 
"""
import logging

import allure
import pytest

from page_objects.wan_android_home import HomePage
from page_objects.wan_android_sidebar import ViewsPage

# 配置日志
logger = logging.getLogger(__name__)

@allure.epic("ApiDemos")
@allure.feature("登录认证模块")
class TestApiDemos:
    @allure.story("常规登录场景")
    @allure.title("使用合法账号登录成功")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.description("""
        验证用户在正常网络环境下：
        1. 处理初始化弹窗和广告
        2. 选择证券登录类型
        3. 输入正确凭证后成功跳转至‘交易’首页
        """)
    @allure.link("https://docs.example.com/login_spec", name="登录业务说明文档")
    @allure.issue("BUG-1001", "已知偶发：部分机型广告Banner无法滑动")
    def test_api_demos_success(self, driver,user):
        """
        测试场景：使用正确的用户名和密码登录成功
        """
        api_demos = HomePage(driver)

        # 执行业务逻辑
        api_demos.click_text()
        api_demos.click_unicode()
        # 断言部分使用 allure.step 包装，使其在报告中也是一个可读的步骤
        with allure.step("最终校验：检查是否进入首页并显示‘交易’标题"):
            actual_text = api_demos.get_home_text()
            assert actual_text == "Text"

        # 页面跳转
        api_demos.go_to(ViewsPage).screenshot_views()
        api_demos.delay(5)