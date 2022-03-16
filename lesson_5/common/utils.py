"""Утилиты"""

import json
import re
import sys

sys.path.append('../')

from common.variables import MAX_PACKAGE_LENGTH, ENCODING

def get_message(client):
    '''
    Утилита приёма и декодирования сообщения
    принимает байты выдаёт словарь, если приняточто-то другое отдаёт ошибку значения
    :param client:
    :return:
    '''

    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


def send_message(sock, message):
    '''
    Утилита кодирования и отправки сообщения
    принимает словарь и отправляет его
    :param sock:
    :param message:
    :return:
    '''
    if not isinstance(message, dict):
        raise TypeError
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)

def valid_ip(address):
    '''Валидация IP адреса'''
    try:
        m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", address)
        if bool(m) and all(map(lambda n: 0 <= int(n) <= 255, m.groups())):
            return True
        else: raise TypeError
    except TypeError:
        if address == 'localhost':
            return True
        else:
            LOGGER.critical(f'Неверный формат введенного IP адреса {address}', exc_info=True)
            return False

