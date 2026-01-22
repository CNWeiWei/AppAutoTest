import logging
from functools import wraps
from typing import Union, Callable

logger = logging.getLogger(__name__)

def resolve_wait_method(func):
    """
    装饰器：将字符串形式的等待条件解析为可调用的 EC 对象
    """
    @wraps(func)
    def wrapper(self, method: Union[Callable, str], *args, **kwargs):
        if isinstance(method, str):
            # TODO: 这里可以接入 custom_ec 字典进行查找
            # method = custom_ec.get(method, lambda x: False)
            logger.info(f"解析命名等待条件: '{method}'")
            # 保持原有逻辑作为占位
            method = lambda _: False
        return func(self, method, *args, **kwargs)
    return wrapper