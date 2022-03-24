"""Программа-сервер"""
import argparse
import socket
import sys
import json
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE
from common.utils import get_message, send_message
from logs.config_server_log import LOGGER

def process_client_message(message):
    '''
    Обработчик сообщений от клиентов, принимает словарь -
    сообщение от клинта, проверяет корректность,
    возвращает словарь-ответ для клиента

    :param message:
    :return:
    '''
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
            and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
        LOGGER.info('Сообщение от клиента прошло валидацию')
        return {RESPONSE: 200}
    LOGGER.error(f'Сообщение от клиента {message} не прошло валидацию')
    return {
        RESPONDEFAULT_IP_ADDRESSSE: 400,
        ERROR: 'Bad Request'
    }


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--addr', nargs='?', default="", help='Укажите адрес доступный для клиента, по умолчанию будет указан адрес ""')
    parser.add_argument('-p', '--port', nargs='?', default='7777', help='Укажите номер порта сервера, по умолчанию будет указан порт 7777')
    args = parser.parse_args()
    param_names = [param_name for param_name, _ in vars(args).items()]

    try:
        if 'port' in param_names:
            listen_port = int(args.port)

        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except TypeError:
        LOGGER.critical(f'После параметра -\'p\' необходимо указать номер порта.')
        sys.exit(1)
    except ValueError:
        LOGGER.error(
            f'Попытка запуска сервера с неподходящим номером порта: {listen_port}.'
            f' Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    # Затем загружаем какой адрес слушать

    try:
        if 'addr' in param_names:
            listen_address = args.addr
        else:
            raise IndexError
    except IndexError:
        LOGGER.error(
            'После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
        sys.exit(1)

    # Готовим сокет

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    transport.bind((listen_address, listen_port))
    # Слушаем порт

    transport.listen(MAX_CONNECTIONS)

    while True:
        client, client_address = transport.accept()
        LOGGER.info(f'Установлено соединение с клиентом: {client_address}')
        try:
            message_from_cient = get_message(client)
            LOGGER.info(f'Получено сообщение от клиента {message_from_cient}')
            response = process_client_message(message_from_cient)
            send_message(client, response)
            LOGGER.info(f'Отправлен ответ клиенту {response}')
            client.close()
        except (ValueError, json.JSONDecodeError):
            LOGGER.error('Принято некорретное сообщение от клиента.')
            client.close()


if __name__ == '__main__':
    main()
