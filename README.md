# AppAutoTest

设备能力配置 (Capabilities)

```python
ANDROID_CAPS = {
    "platformName": "Android",
    "automationName": "uiautomator2",
    "deviceName": "Android",
    "appPackage": "com.android.settings",
    "appActivity": ".Settings",
    "noReset": False
}
```

| 字段名称           | 字段含义解释                                      | 示例值说明                                                                                 |
|----------------|---------------------------------------------|---------------------------------------------------------------------------------------|
| platformName   | 测试的平台/操作系统。这是必填项，告诉自动化框架（如Appium）目标是什么系统。   | "Android" 表示这是一个Android设备。如果是iOS设备，则为 "iOS"。                                          |
| automationName | 使用的自动化驱动引擎。指定底层用哪个工具来驱动设备进行UI交互。            | "uiautomator2" 是当前主流的Android驱动框架，比旧的 "UiAutomator" 更稳定和高效。                            |
| deviceName     | 设备标识/名称。用于在同时连接多台设备时指定目标。                   | "Android" 是一个通用标识。在实际测试中，通常用 adb devices 获取的真实设备序列号（如 emulator-5554）来替换它，以确保连接到正确的设备。 |
| appPackage     | 要测试的应用程序包名。这是应用的唯一标识，就像它在Android系统中的“身份证号”。 | "com.android.settings" 是Android系统“设置”应用的包名。测试你自己的应用时，需替换为你应用的包名。                      |
| appActivity    | 要启动的应用内具体页面。它指定了应用启动后打开的第一个界面（Activity）。    | ".Settings" 是“设置”应用的主界面。前面的点. 表示它是 appPackage 下的一个相对路径。                               |

获取应用的 appPackage 有几种常用方法

```shell
adb shell pm list packages | findstr your_package_name
# adb shell pm list packages -3 仅列出用户安装的第三方应用的包名
```

获取应用的 appActivity 有几种常用方法

```shell
# 1，使用 aapt 工具分析 APK 文件（需有安装包）/build-tools/{version}/aapt
aapt dump badging your_app.apk | findstr launchable-activity
# 输出结果：launchable-activity: name='com.example.myapp.MainActivity'
# name= 后面的值 'com.example.myapp.MainActivity' 就是你需要的主 Activity

# 2，通过 ADB 命令获取（需应用已安装）
adb shell dumpsys window | findstr mCurrentFocus
# 输出结果：mCurrentFocus=Window{... u0 com.example.myapp/com.example.myapp.MainActivity}
# / 后面的部分 com.example.myapp.MainActivity 就是当前 Activity
```

常用补充字段：
noReset：True/False。是否在会话开始前重置应用状态（例如清除应用数据）。设置为 True 可以避免每次测试都重新登录。

platformVersion：指定设备的Android系统版本（如 "11.0"）。虽然不是必须，但指定后能增强兼容性。

unicodeKeyboard 和 resetKeyboard：用于处理中文输入等特殊字符输入。

newCommandTimeout：设置Appium服务器等待客户端发送新命令的超时时间（秒），默认为60秒。在长时间操作中可能需要增加。