#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: report_handler
@date: 2026/2/3 13:51
@desc: 
"""
import logging
import subprocess
import shutil

from core.settings import ALLURE_TEMP, REPORT_DIR

logger = logging.getLogger(__name__)


def generate_allure_report() -> bool:
    """
    将 JSON 原始数据转换为 HTML 报告
    """
    if not ALLURE_TEMP.exists() or not any(ALLURE_TEMP.iterdir()):
        logger.warning("未发现 Allure 测试数据，跳过报告生成。")
        return False

    # 检查环境是否有 allure 命令行工具
    if not shutil.which("allure"):
        logger.error("系统未安装 Allure 命令行工具，请先安装：https://allurereport.org/docs/")
        return False

    try:
        logger.info("正在生成 Allure HTML 报告...")
        # --clean 会清理掉 REPORT_DIR 里的旧报告
        subprocess.run(
            f'allure generate "{ALLURE_TEMP}" -o "{REPORT_DIR}" --clean',
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Allure 报告已生成至: {REPORT_DIR}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Allure 报告生成失败: {e.stderr}")
        return False
