import time

from appium import webdriver
from appium.options.android import UiAutomator2Options

from run_appium import start_appium_service, stop_appium_service, with_appium


@with_appium
def main(service):
    print(f"正在测试，服务模式: {service.role}")
    # 简单操作示例
    driver = None
    try:
        # 在自动化套件启动前执行
        # proc = start_appium_service()

        # 配置Android设备参数
        capabilities = dict(
            platformName='Android',
            automationName='uiautomator2',
            deviceName='Android',
            appPackage='com.android.settings',
            appActivity='.Settings'
        )

        # 转换capabilities为Appium Options
        options = UiAutomator2Options().load_capabilities(capabilities)

        # 连接Appium服务器
        # driver = webdriver.Remote('http://localhost:4723', options=options)
        driver = webdriver.Remote('http://127.0.0.1:4723', options=options)
        time.sleep(1)
        print("当前Activity:", driver.current_activity)
    finally:
        driver.quit()
        # 在自动化套件结束后执行
        # stop_appium_service(proc)
    print("Hello from AppAutoTest!")


if __name__ == "__main__":
    main()
