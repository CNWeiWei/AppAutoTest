# AppAutoTest - 基于 Python 的 App 自动化测试框架

## 1. 简介

`AppAutoTest` 是一个基于 Python 构建的健壮且可扩展的移动应用自动化测试框架。它利用 Appium、Pytest 和 Allure 等行业标准工具，为测试
Android 和 iOS 应用提供了全面的解决方案。该框架采用页面对象模型 (POM) 设计，以提高可维护性和可扩展性，并包含一套实用工具以简化测试开发和执行。

## 2. 特性

- **跨平台支持**: 原生支持 Android (通过 `UiAutomator2`) 和 iOS (通过 `XCUITest`)。
- **页面对象模型 (POM)**: 强制分离 UI 元素定位器和测试逻辑，增强代码可读性和可维护性。
- **丰富的测试报告**: 与 Allure 框架无缝集成，生成包含测试步骤、截图、日志和环境信息的详细交互式报告。
- **自动服务管理**: 智能管理 Appium 服务器生命周期。如果本地服务器未运行，它可以自动启动，或者连接到现有的外部服务器。
- **强大的驱动引擎**: 包含核心驱动封装 (`CoreDriver`)，通过内置显式等待、流式 API、高级日志记录和健壮的错误处理简化 Appium
  操作。
- **灵活配置**: 轻松管理设备能力 (`config/caps.yaml`)、特定环境参数和敏感数据 (`.env`)。
- **可自定义等待条件**: 扩展 Selenium 的标准预期条件，提供用于复杂场景（如等待 Toast 消息或特定元素计数）的自定义可重用等待。
- **高级日志与追踪**: 利用自定义装饰器 (`@step_trace`) 自动生成测试步骤的分层日志，包括执行时间、输入参数和状态。
- **自动截图**: 在测试失败时自动捕获截图，并允许在任何步骤轻松将截图附加到 Allure 报告中以便快速调试。
- **现代依赖管理**: 使用 `uv` (通过 `pyproject.toml`) 进行快速 Python 依赖解析，使用 `npm` (通过 `package.json`) 管理
  Node.js 依赖。

## 3. 项目结构

框架遵循逻辑清晰且模块化的结构，以促进可扩展性和易于导航。

```text
AppAutoTest/
├── config/
│   └── caps.yaml             # 不同平台的 Appium capabilities 配置。
├── core/
│   ├── base_page.py          # 所有页面对象的抽象基类。
│   ├── config_loader.py      # 加载配置文件 (caps, 环境设置)。
│   ├── custom_expected_conditions.py # 定义复杂 UI 状态的自定义等待条件。
│   ├── driver.py             # 核心 Appium 驱动封装，增强了操作和等待。
│   ├── modules.py            # 通用枚举定义 (如 AppPlatform, Locator)。
│   ├── run_appium.py         # 处理 Appium 服务器的生命周期。
│   └── settings.py           # 全局框架设置 (路径, 超时等)。
├── data/                     # 数据驱动测试的示例测试数据。
├── docs/                     # 文档和说明。
├── outputs/
│   ├── logs/                 # 存储测试运行的日志文件。
│   └── screenshots/          # 存储测试期间捕获的截图。
├── page_objects/             # 对象类。
├── reports/                  # 存储生成的 Allure HTML 报告。
├── temp/                     # 原始 Allure 结果的临时目录。
├── test_cases/               # 测试脚本。
├── utils/
│   ├── decorators.py         # 用于日志、截图等的自定义装饰器。
│   ├── dirs_manager.py       # 确保所需目录存在的工具。
│   ├── finder.py             # 定位策略转换工具。
│   └── report_handler.py     # Allure 报告生成工具。
├── .env                      # 存储环境变量 (如凭据)。Git 忽略此文件。
├── conftest.py               # Pytest 的核心配置文件，用于 fixtures 和 hooks。
├── main.py                   # 执行测试套件的主入口点。
├── package.json              # 定义 Node.js 项目元数据和依赖 (Appium)。
├── pytest.ini                # Pytest 配置文件 (日志, 标记, 路径)。
├── pyproject.toml            # Python 项目元数据和依赖定义 (PEP 621)。
└── README.md                 # 项目说明。
```

## 4. 前置条件

- **Node.js**: 版本 20+ (如 `package.json` 中指定)。
- **Python**: 版本 3.11+ (如 `pyproject.toml` 中指定)。
- **Java JDK**: Appium 和 Android SDK 需要。
- **Android SDK**: 构建和与 Android 应用交互需要。
- **Allure Commandline**: 生成和查看 HTML 报告需要。
> 注意：[Android SDK 环境配置指南](docs/AndroidSDK环境配置指南.md)
## 5. 安装与运行指南

按照以下步骤搭建测试环境。

1. **克隆仓库:**
   ```bash
   git clone https://github.com/CNWeiWei/AppAutoTest
   cd AppAutoTest
   ```

2. **安装 Node.js 依赖:**
   此命令将在项目目录中本地安装 Appium 及其相关驱动，如 `package.json` 中所定义。
   ```bash
   npm install
   ```

3. **安装 Python 依赖:**
   使用 `uv` 进行 Python 依赖管理。
   ```bash
   # 如果没有安装 uv，请先安装
   # 使用 uv 安装项目依赖
   uv sync
   ```
   不使用 `uv`进行 Python 依赖管理。
   ```bash
   #使用 pip 安装项目依赖
   # 以可编辑模式安装（开发时推荐）
    pip install -e .
    
    # 或以普通模式安装
    pip install .
   ```

## 6. 如何运行测试

框架提供了两种主要的测试执行方式。

### 方法 1: 使用主入口点 (推荐)

执行 `main.py` 脚本来运行整个测试套件。此脚本会自动处理所有运行前和运行后的任务。

```bash
python main.py
```

此命令将：

1. 确保所有必要的输出目录已创建。
2. 归档上次运行的日志文件。
3. 启动 Appium 服务器 (或连接到现有的)。
4. 通过 Pytest 运行 `test_cases/` 目录下的所有测试。
5. 在 `reports/` 目录生成新的 Allure 报告。

### 方法 2: 直接使用 Pytest

为了更精细的控制，您可以直接从命令行调用 `pytest`。`conftest.py` 中定义的 fixtures 仍将管理 Appium 服务器和驱动会话。

```bash
# 运行特定的测试文件并显示详细输出
pytest -v test_cases/test_wan_android_home.py

# 运行测试并在第一个失败处停止
pytest -x

# 覆盖默认平台并指定设备 UDID
pytest --platform IOS --udid <your_iphone_udid>
```

**可用的自定义命令行参数:**

- `--platform`: 目标平台 (`Android` 或 `IOS`)。默认为 `Android`。
- `--caps_name`: 设备/平台名称。
- `--udid`: 目标设备的唯一设备标识符 (UDID)。
- `--host`: Appium 服务器的主机地址。默认为 `127.0.0.1`。
- `--port`: Appium 服务器的端口。默认为 `4723`。

> 注意：[其他常用参数](./docs/常用参数.md)

## 7. 测试报告

测试运行后，原始 Allure 结果存储在 `temp/` 目录中。`main.py` 脚本会自动根据这些结果生成 HTML 报告。

要查看最新报告，可以使用 Allure 命令行工具启动服务：

```bash
# 此命令将在默认 Web 浏览器中打开报告
allure serve temp/
```

## 8. 核心概念解释

#### 页面对象模型 (POM)

- **`page_objects/`**: 此目录包含 POM 设计的核心。每个类 (例如 `HomePage`)
  代表应用程序的一个屏幕或重要组件。它负责封装元素定位器和对这些元素执行操作的方法 (例如 `login(user, pwd)`)。
- **`core/base_page.py`**: 这是所有页面对象的父类。它提供共享功能，如页面间导航 (`go_to`)、将截图附加到报告 (
  `attach_screenshot_bytes`) 以及实现通用断言 (`assert_text`)。

#### 驱动引擎

- **`core/driver.py`**: 此类是标准 Appium `webdriver.Remote` 的强大封装。它通过集成内置的显式等待增强了基本操作，使测试更稳定，更不容易出现竞争条件。它还为高级移动手势（如
  `swipe()`、`long_press()` 和 `smart_scroll()`）提供了流畅的接口。

#### 自定义装饰器

- **`utils/decorators.py`**: 此模块包含装饰器，可在不干扰逻辑的情况下向测试和页面方法添加强大的横切关注点。
    - `@step_trace()`: 自动记录任何被装饰函数的进入、退出、参数和执行时间，创建一个清晰的分层日志，这对调试非常有价值。
    - `@action_screenshot()`: 一个简单但有效的装饰器，在方法成功执行后自动截图，在测试报告中提供可视化的审计跟踪。