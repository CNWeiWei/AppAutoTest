import os
import shutil
import datetime
from pathlib import Path

import pytest

from core.settings import LOG_SOURCE, LOG_BACKUP_DIR, ALLURE_TEMP, REPORT_DIR
# 日志自动清理
def _clean_old_logs(backup_dir, keep_count=10):
    files = sorted(Path(backup_dir).glob("pytest_*.log"), key=os.path.getmtime)
    while len(files) > keep_count:
        os.remove(files.pop(0))


def main():
    try:
        # 2. 执行 Pytest
        # 建议保留你之前配置的 -s -v 等参数
        exit_code = pytest.main(["test_cases", "-x", "-v", f"--alluredir={ALLURE_TEMP}"])

        # 3. 生成报告
        if ALLURE_TEMP.exists():
            os.system(f'allure generate {ALLURE_TEMP} -o {REPORT_DIR} --clean')

    finally:
        # 4. 备份日志 (无论测试是否崩溃都执行)
        if LOG_SOURCE.exists():
            now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = LOG_BACKUP_DIR / f"pytest_{now}.log"
            shutil.copy2(LOG_SOURCE, backup_path)
            print(f"日志已备份至: {backup_path}")
            _clean_old_logs(LOG_BACKUP_DIR)
        else:
            print("未找到原始日志文件，跳过备份。")


if __name__ == "__main__":
    main()
