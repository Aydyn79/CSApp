import sys
from functools import wraps

sys.path.append('../logs/')
from logs.config_log_1 import LOGGER


def log(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        args_rep = [repr(arg) for arg in args]
        kwargs_rep = [f"{k}={v!r}" for k, v in kwargs.items()]
        sig = ", ".join(args_rep + kwargs_rep)
        val = func(*args, **kwargs)
        LOGGER.info(f'Обращение к функции {func.__name__}, с аргументами ({sig})')
        return val

    return wrapper

@log
def bye(*args, **kwargs):
    '''Функция просто распечатывает арги'''
    for item in args:
        print(f"Hello {item}")
    for key, val in kwargs.items():
        print(f"Hello {key} bye {val}")


a = ['andry', 'kevin', 'goblin']
b = {'ODKB': 'NATO', 'Russia': 'Europa', 'China': 'West'}
bye(*a,**b)


@log
def hello(name):
    print(f"Hello {name}")


hello('name')

class Log:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        args_rep = [repr(arg) for arg in args]
        kwargs_rep = [f"{k}={v!r}" for k, v in kwargs.items()]
        sig = ", ".join(args_rep + kwargs_rep)
        LOGGER.info(f'Обращение к функции {self.func.__name__}, с аргументами {sig}')
        self.func(*args, **kwargs)


@Log
def hi(name):
    return print(f"Hello {name}")

hi('my friends')

@Log
def bye(*args, **kwargs):
    '''Функция просто распечатывает арги'''
    for item in args:
        print(f"Hello {item}")
    for key, val in kwargs.items():
        print(f"Hello {key} bye {val}")


a = ['andry', 'kevin', 'goblin']
b = {'ODKB': 'NATO', 'Russia': 'Europa', 'China': 'West'}
bye(*a,**b)