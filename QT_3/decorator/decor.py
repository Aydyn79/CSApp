import inspect
import logging
import os
import sys
from functools import wraps
sys.path.append('../logs/')
from logs.config_client_log import LOGGER

def logged(cls=None,*, name=""):
    def logged_for_init(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

            # Подготовка имени файла для логирования
            PATH = os.path.dirname(os.path.abspath(__file__))
            PATH = os.path.join(PATH, 'client_s.log')

            # создаём потоки вывода логов
            STREAM_HANDLER = logging.StreamHandler(sys.stderr)
            STREAM_HANDLER.setFormatter(FORMATTER)
            STREAM_HANDLER.setLevel(logging.ERROR)
            LOG_FILE = logging.FileHandler(PATH, encoding='utf8')
            LOG_FILE.setFormatter(FORMATTER)

            logger_name = name or self.__class__.__name__

            self.log = logging.getLogger(logger_name)
            self.log.addHandler(STREAM_HANDLER)
            self.log.addHandler(LOG_FILE)
            self.log.setLevel(logging.INFO)
            self.log.info(f'Создан экземпляр класса {cls.__name__}')
            return func(self, *args, **kwargs)

        return wrapper

    def wrap(cls):
        cls.__init__ = logged_for_init(cls.__init__)
        print('Hooo')
        return cls

    return wrap if cls is None else wrap(cls)


@logged
class MyClass:
    def __init__(self):
        self.log.info(f"We need to go deeper {inspect.stack()}")
        # self.log.info(f"Создан объект класса {}")

@logged
def Some_func():
    print('Hi')

cl = MyClass()
Some_func()
