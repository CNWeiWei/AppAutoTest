#!/usr/bin/env python
# coding=utf-8

"""
@author: CNWei,ChenWei
@Software: PyCharm
@contact: t6g888@163.com
@file: main
@date: 2026/1/13 16:54
@desc:
"""
import shutil
import datetime
from pathlib import Path

import pytest

from core.settings import LOG_SOURCE, LOG_BACKUP_DIR, ALLURE_TEMP
from utils.dirs_manager import ensure_dirs_ok
from utils.report_handler import generate_allure_report


# netstat -ano | findstr :4723
# taskkill /PID 12345 /F

def _archive_logs():
    """
    在测试开始前，归档上一次运行的日志文件。
    此时没有任何句柄占用，move 操作是 100% 安全的。
    """
    # 4. 备份日志 (无论测试是否崩溃都执行)
    if LOG_SOURCE.exists() and LOG_SOURCE.stat().st_size > 0:
        now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = LOG_BACKUP_DIR / f"pytest_{now}.log"
        try:
            # 移动并重命名
            shutil.move(str(LOG_SOURCE), str(backup_path))
            print(f"已自动归档上次运行的日志: {backup_path}")
            # shutil.copy2(LOG_SOURCE, backup_path)
            # print(f"日志已备份至: {backup_path}")
            _clean_old_logs(LOG_BACKUP_DIR)
        except Exception as e:
            print(f"归档旧日志失败 (可能被外部编辑器打开): {e}")
    else:
        print("未找到原始日志文件，跳过备份。")

# 日志清理
def _clean_old_logs(backup_dir, keep_count=10):
    files = sorted(Path(backup_dir).glob("pytest_*.log"), key=lambda p: p.stat().st_mtime)
    while len(files) > keep_count:
        file_to_remove = files.pop(0)
        try:
            file_to_remove.unlink(missing_ok=True)
        except OSError as e:
            print(f"清理旧日志失败 {file_to_remove}: {e}")

def _clean_temp_dirs():
    """
    可选：如果你想在测试前清理掉旧的临时文件
    """
    if ALLURE_TEMP.exists():
        shutil.rmtree(ALLURE_TEMP)
        # 加上 ignore_errors 是为了防止文件被占用导致整个测试无法启动
        shutil.rmtree(ALLURE_TEMP, ignore_errors=True)
    ALLURE_TEMP.mkdir(parents=True, exist_ok=True)

def main():
    try:
        # 1. 创建目录
        ensure_dirs_ok()

        # 2. 处理日志
        _archive_logs()

        # 3. 执行 Pytest
        # 注意：-x 表示遇到错误立即停止，如果是全量回归建议去掉 -x
        pytest.main(["test_cases", "-x", "-v", f"--alluredir={ALLURE_TEMP}"])

        # 4. 生成报告
        generate_allure_report()
    except Exception as e:
        print(f"自动化测试执行过程中发生异常: {e}")

    finally:
        print("Time-of-check to Time-of-use")


if __name__ == "__main__":
    main()
