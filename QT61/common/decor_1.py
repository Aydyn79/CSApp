import socket
import sys
from functools import wraps

sys.path.append('../logs/')
from logs.config_log_2 import LOGGER


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

# @log
# def bye(*args, **kwargs):
#     '''Функция просто распечатывает арги'''
#     for item in args:
#         print(f"Hello {item}")
#     for key, val in kwargs.items():
#         print(f"Hello {key} bye {val}")


# a = ['andry', 'kevin', 'goblin']
# b = {'ODKB': 'NATO', 'Russia': 'Europa', 'China': 'West'}
# bye(*a,**b)

#
# @log
# def hello(name):
#     print(f"Hello {name}")
#

# hello('name')

class Log:
    '''
    Класс-декоратор логирующий имя функции и перечень аргументов
    '''
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        args_rep = [repr(arg) for arg in args]
        kwargs_rep = [f"{k}={v!r}" for k, v in kwargs.items()]
        sig = ", ".join(args_rep + kwargs_rep)
        LOGGER.info(f'Обращение к функции {self.func.__name__}, с аргументами {sig}')
        self.func(*args, **kwargs)



def login_required(func):
    """
    Декоратор, проверяющий, что клиент авторизован на сервере.
    Проверяет, что передаваемый объект сокета находится в
    списке авторизованных клиентов.
    За исключением передачи словаря-запроса
    на авторизацию. Если клиент не авторизован,
    генерирует исключение TypeError
    """

    def checker(*args, **kwargs):
        # проверяем, что первый аргумент - экземпляр MessageProcessor
        # Импортить необходимо тут, иначе ошибка рекурсивного импорта.
        from server.msg_processor import MessageProcessor
        from common.variables import ACTION, PRESENCE
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    # Проверяем, что данный сокет есть в списке names класса
                    # MessageProcessor
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            # Теперь надо проверить, что передаваемые аргументы не presence
            # сообщение. Если presence, то разрешаем
            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            # Если не не авторизован и не сообщение начала авторизации, то
            # вызываем исключение.
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker

