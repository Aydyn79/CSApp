"""Константы"""

# Порт поумолчанию для сетевого ваимодействия
import logging

# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
USER_REQUEST = 'get_users'
LIST_INFO = 'data_list'
GET_CONTACTS = 'get_contacts'
ADD_CONTACT = 'add_contact'
DEL_CONTACT = 'del_contact'
ERROR = 'error'
RESPONDEFAULT_IP_ADDRESSSE = 'respondefault_ip_addressse'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
EXIT = 'exit'


DEFAULT_PORT = 7777
# IP адрес по умолчанию для подключения клиента
DEFAULT_IP_ADDRESS = '127.0.0.1'
# Максимальная очередь подключений
MAX_CONNECTIONS = 5
# Максимальная длинна сообщения в байтах
MAX_PACKAGE_LENGTH = 1024
# Кодировка проекта
ENCODING = 'utf-8'
# Текущий уровень логирования
LOGGING_LEVEL = logging.DEBUG
# Ответ 200
RESPONSE_200 = {RESPONSE: 200}
# Ответ 400
RESPONSE_400 = {RESPONSE: 400, ERROR: None}
# 202-й ответ
RESPONSE_202 = {RESPONSE: 202,
                LIST_INFO: None}

# Прококол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'

