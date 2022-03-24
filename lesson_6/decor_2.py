import functools
import inspect
import sys
import threading
import traceback

from logs.config_log_2 import LOGGER
from datetime import datetime


def log(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        val = func(*args, **kwargs)
        name_f = func.__name__
        LOGGER.info(f' - Функция {name_f} вызвана из функции {inspect.stack()[1][3]}')
        LOGGER.info(f'Альтернативное определение вызывающей функции №1: {sys._getframe().f_back.f_code.co_name}')
        LOGGER.info(f'Альтернативное определение вызывающей функции №2: '
                    f'{traceback.format_stack()[0].strip().split()[-1]}.')
        LOGGER.info(f'Вызов {name_f} из модуля: {inspect.stack()[0][1].split("/")[-1]}.')
        LOGGER.info(f'Альтернативное определение вызывающего модуля (Для тех кто не ищет легких путей):'
                    f'{sys._getframe().f_back.f_code.co_filename.split("/")[-1]}')

        return val
    return wrapper


@log
def hello(name):
    "Hello from the other side."
    return f"Hello {name}"


def ex(name):
    hello(name)


ex('andry')


thread = threading.Thread(target=ex, args=('The Victor'))
print(thread.getName())