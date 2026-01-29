import logging
from functools import wraps
from typing import Union, Callable


from core.custom_expected_conditions import get_condition


logger = logging.getLogger(__name__)


def resolve_wait_method(func):
    """
    装饰器：将字符串形式的等待条件解析为可调用的 EC 对象
    """

    @wraps(func)
    def wrapper(self, method: Union[Callable, str], *args, **kwargs):
        if isinstance(method, str):
            # 解析格式 "key:arg1,arg2" 或 仅 "key"
            ec_name = method
            ec_args = []

            if ":" in method:
                ec_name, params = method.split(":", 1)
                if params:
                    ec_args = params.split(",")

            # 委托给 core.custom_expected_conditions.get_condition 处理
            try:
                logger.info(f"解析命名等待条件: '{ec_name}' 参数: {ec_args}")
                method = get_condition(ec_name, *ec_args)
            except Exception as e:
                logger.error(f"解析等待条件 '{method}' 失败: {e}")
                raise e

        return func(self, method, *args, **kwargs)

    return wrapper