#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: test_wan_android_project
@date: 2026/1/30 17:42
@desc: 
"""
import logging

import allure

from page_objects.wan_android_project import ProjectPage

# 配置日志
logger = logging.getLogger(__name__)


@allure.epic("测试用例示例")
@allure.feature("项目模块")
class TestWanAndroidProject:
    @allure.story("项目切换场景")
    @allure.title("切换项目页面")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("""
        验证滑动切换项目页面展示：
        1. XXXXX
        2. XXXXXXXXXXX
        """)
    @allure.link("https://docs.example.com/login_spec", name="项目业务说明文档")
    @allure.issue("BUG-1002", "已知偶发：我是一个bug")
    def test_project_slide_success(self, driver):
        """
        测试场景：验证页面滑动
        """
        project = ProjectPage(driver)

        # 执行业务逻辑
        project.switch_to_project()
        project.slide_views()

        # 断言部分使用 allure.step 包装，使其在报告中也是一个可读的步骤
        with allure.step("断言"):
            assert 1 == 1

        project.delay(5)
