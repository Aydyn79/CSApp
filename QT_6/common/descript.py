import logging
import re

from config_server_log import LOGGER

logger = logging.getLogger('server_dist')

# def valid_ip(address):
#     '''Валидация IP адреса'''
#     try:
#         m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", address)
#         if bool(m) and all(map(lambda n: 0 <= int(n) <= 255, m.groups())):
#             return True
#         else: raise TypeError
#     except TypeError:
#         if address == 'localhost':
#             return True
#         else:
#             LOGGER.critical(f'Неверный формат введенного IP адреса {address}', exc_info=True)
#             return False


class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            logger.critical(
                f'Попытка запуска сервера с указанием неподходящего порта {value}. Допустимы адреса с 1024 до 65535.')
            exit(1)
        # Если порт прошёл проверку, добавляем его в список атрибутов экземпляра
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        # owner - <class '__main__.Server'>
        # name - port
        self.name = name

class Address:
    def __set__(self, instance, value):
        if value != '':
            logger.critical(
                f'Попытка запуска сервера с указанием неправильного формата адреса {value}.')
            exit(1)
        # Если адрес прошёл проверку, добавляем его в список атрибутов экземпляра
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name