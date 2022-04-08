import functools
import inspect
from logs.config_log_2 import LOGGER

def log(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        val = func(*args, **kwargs)
        name_f = func.__name__
        LOGGER.info(f' - Функция {name_f} вызвана из функции {inspect.stack()[1][3]}')
        LOGGER.info(f'Вызов {name_f} из модуля: {inspect.stack()[0][1].split("/")[-1]}.')
        return val
    return wrapper
