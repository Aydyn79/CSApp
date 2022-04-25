"""Константы"""

# Порт поумолчанию для сетевого ваимодействия
import logging

# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
RESPONDEFAULT_IP_ADDRESSSE = 'respondefault_ip_addressse'
MESSAGE_TEXT = 'mess_text'

# Прококол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'
USER_REQUEST = 'get_users'
LIST_INFO = 'data_list'
GET_CONTACTS = 'get_contacts'
ADD_CONTACT = 'add_contact'
DEL_CONTACT = 'del_contact'
MESSAGE = 'message'
EXIT = 'exit'
REMOVE_CONTACT = 'remove'
DATA = 'binary'
PUBLIC_KEY = 'the_secret_of_the_Madrid_Court'
USERS_REQUEST = 'get_users'
PUBLIC_KEY_REQUEST = 'pubkey_need'



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
# 202-й ответ для функции contacts_list_update в модуле net_client
RESPONSE_202 = {RESPONSE: 202,
                LIST_INFO: None}
# 205-й ответ для функции
RESPONSE_205 = {RESPONSE: 205}

# 511-й ответ для функции
RESPONSE_511 = {RESPONSE: 511,
                DATA: None}

# База данных для хранения данных сервера:
SERVER_CONFIG = 'server_dist+++.ini'


