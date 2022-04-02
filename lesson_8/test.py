
import argparse
import logging
import sys
import json
import socket
import threading
import time
from errors import *
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, EXIT, DESTINATION, MESSAGE, MESSAGE_TEXT, SENDER
from common.utils import get_message, send_message, valid_ip

from decor_2 import log
from logs.config_client_log import LOGGER


def create_message(account_name='Guest'):
    to_user = input('Введите получателя сообщения: ')
    message = input('Введите сообщение для отправки: ')
    message_dict = {
        ACTION: MESSAGE,
        SENDER: account_name,
        DESTINATION: [to_user],
        TIME: time.time(),
        MESSAGE_TEXT: message
    }
    print(f'Сформирован словарь сообщения: {message_dict}')
    return message_dict


# create_message(account_name='Guest')
to_user = input('Введи : ')
if ',' in to_user:
    to_user=tuple(i.strip() for i in to_user.split(','))
elif ' ' in to_user:
    to_user = tuple(to_user.split())
message = {
        ACTION: MESSAGE,
        SENDER: 'test1',
        DESTINATION: to_user,
        TIME: time.time(),
        MESSAGE_TEXT: 'message'
    }
print(len(message[DESTINATION])) if message[DESTINATION] is tuple else 0

print(type(message[DESTINATION]))
for i in message[DESTINATION]:
    print(i)