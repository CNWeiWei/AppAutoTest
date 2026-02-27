#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: test_wan_android_home
@date: 2026/1/30 17:42
@desc: 
"""
import logging
import os

import allure
from dotenv import load_dotenv

from page_objects.wan_android_home import HomePage
from page_objects.wan_android_project import ProjectPage

load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)


@allure.epic("测试用例示例")
@allure.feature("登录模块")
class TestWanAndroidHome:
    @allure.story("常规登录场景")
    @allure.title("使用合法账号登录成功")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.description("""
        验证用户在正常网络环境下：
        1. 处理初始化弹窗和广告
        2. 输入正确账号密码后成功登录
        """)
    @allure.link("https://docs.example.com/login_spec", name="登录业务说明文档")
    @allure.issue("BUG-1001", "已知偶发：我是一个bug")
    def test_api_demos_success(self, driver):
        """
        测试场景：使用正确的用户名和密码登录成功
        """
        home = HomePage(driver)

        # 执行业务逻辑
        home.click_open()

        home.login(os.getenv("USER_NAME"), os.getenv("PASS_WORD"))

        # 断言部分使用 allure.step 包装，使其在报告中也是一个可读的步骤
        with allure.step("断言"):
            assert os.getenv("USER_NAME") == 'admintest123456'


        # 页面跳转
        with allure.step("验证页面跳转"):
            project = home.go_to(ProjectPage)
            project.switch_to_project()
            project.assert_text(*project.pro_table_title,expected_text='完整项目')

        project.delay(5)
