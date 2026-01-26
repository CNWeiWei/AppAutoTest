#!/usr/bin/env python
# coding=utf-8

"""
@desc: 模拟登录功能测试用例
"""
import pytest
import logging
from core.driver import CoreDriver
from core.modules import AppPlatform

# 配置日志
logging.basicConfig(level=logging.INFO)

class TestLogin:
    
    driver: CoreDriver = None

    def setup_method(self):
        """
        每个测试用例开始前执行：初始化 Driver 并连接设备
        """
        # 定义测试设备的 Capabilities
        # 注意：实际使用时，appPackage 和 appActivity 需要替换为被测 App 的真实值
        caps = {
            "platformName": "Android",
            "automationName": "UiAutomator2",
            "deviceName": "Android Emulator",
            "appPackage": "com.example.android.apis",  # 替换为你的 App 包名
            "appActivity": ".ApiDemos",                # 替换为你的 App 启动 Activity
            "noReset": True,                           # 不清除应用数据
            "newCommandTimeout": 60
        }

        self.driver = CoreDriver()
        # 连接 Appium Server
        self.driver.server_config(host="127.0.0.1", port=4723)
        self.driver.connect(platform=AppPlatform.ANDROID, caps=caps)

    def teardown_method(self):
        """
        每个测试用例结束后执行：退出 Driver
        """
        if self.driver:
            self.driver.quit()

    def test_login_success(self):
        """
        测试场景：使用正确的用户名和密码登录成功
        """
        # 1. 定位元素信息 (建议后续抽离到 Page Object 层)
        # 假设登录页面的元素 ID 如下：
        input_user = "id:com.example.app:id/et_username"
        input_pass = "id:com.example.app:id/et_password"
        btn_login = "id:com.example.app:id/btn_login"
        txt_welcome = "xpath://*[@text='登录成功']"

        # 2. 执行操作步骤
        # 显式等待并输入用户名
        self.driver.input(input_user, "", "test_user_001")
        
        # 输入密码 (开启敏感模式，日志中脱敏)
        self.driver.input(input_pass, "", "Password123!", sensitive=True)
        
        # 点击登录按钮
        self.driver.click(btn_login, "")

        # 3. 断言结果
        # 方式 A: 检查特定文本是否存在
        # self.driver.assert_text(txt_welcome, "", "登录成功")
        
        # 方式 B: 检查跳转后的页面元素是否可见
        is_login_success = self.driver.is_visible(txt_welcome, "")
        assert is_login_success, "登录失败：未检测到欢迎提示或主页元素"

if __name__ == "__main__":
    # 允许直接运行此文件进行调试
    pytest.main(["-v", "-s", __file__])