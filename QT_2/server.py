"""Программа-сервер"""
import argparse
import select
import socket
import sys
from datetime import time
from pprint import pprint
from threading import Thread
from meta_detect import ServSupervisor
from descript import Port, Address

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE, RESPONSE_400, RESPONSE_200, DESTINATION, \
    MESSAGE, MESSAGE_TEXT, SENDER, EXIT
from common.utils import get_message, send_message
from logs.config_server_log import LOGGER


class Server(metaclass=ServSupervisor):
    port = Port()
    addr = Address()
    def __init__(self, listen_address, listen_port):
        # Параметры подключения
        self.addr = listen_address
        self.port = listen_port

        # Список подключённых клиентов.
        self.clients = []

        # Список сообщений на отправку.
        self.messages = []

        # Словарь содержащий сопоставленные имена и соответствующие им сокеты.
        self.names = dict()

    def init_socket(self):
        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # transport = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.2)
        # Слушаем порт
        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def main_loop(self):
        self.init_socket()

        # Основной цикл программы сервера
        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                LOGGER.info(f'Cоединение не установлено, время для подключения истекло')
                pass
            else:
                LOGGER.info(f'Установлено соединение с клиентом: {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            # сбор клиентов на чтение или запись

            try:
                if self.clients:
                    recv_data_lst, send_data_lst, _ = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except Exception:
                        LOGGER.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        self.clients.remove(client_with_message)
            # Если есть сообщения, обрабатываем каждое.
            for i in self.messages:
                try:
                    # Обработка сообщения для всех клиентов.
                    if i[DESTINATION] == 'for_all':
                        for cli in self.clients:
                            send_message(cli, i)
                    # Обработка сообщения точка-точка.
                    else:
                        self.process_message(i, send_data_lst)
                except Exception:
                    LOGGER.info(f'Связь с клиентом с именем {i[DESTINATION]} была потеряна')
                    self.clients.remove(self.names[i[DESTINATION]])
                    del self.names[i[DESTINATION]]
            self.messages.clear()

    def process_client_message(self, message, client):
        '''
        Обработчик сообщений от клиентов, принимает словарь -
        сообщение от клиента, проверяет корректность,
        возвращает словарь-ответ для клиента
        :param message:
        :param messages_list:
        :param client:
        :param clients:
        :param names:
        :return:
        '''
        LOGGER.debug('Анализ входящего сообщения')
        if ACTION in message and message[ACTION] == PRESENCE and \
                TIME in message and USER in message:
            LOGGER.info('Сообщение от клиента прошло валидацию')
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Имя пользователя уже занято.'
                LOGGER.info(f'Попытка войти в чат под существующим именем \
                    {message[USER][ACCOUNT_NAME]}')
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            LOGGER.info(f'Клиент {message[SENDER]} прислал сообщение {message[MESSAGE_TEXT]} пользователю {message[DESTINATION]}') #Тайна переписки? Неа, не слышал)
            self.messages.append(message)
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            return
        else:
            LOGGER.error(f'Сообщение от клиента {message} не прошло валидацию')
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return

    def process_message(self, message, listen_socks):
        DEST = message[DESTINATION]
        if DEST in self.names and self.names[DEST] in listen_socks:
            send_message(self.names[DEST], message)
            LOGGER.info(f'Отправлено сообщение пользователю {DEST} '
                            f'от пользователя {message[SENDER]}.')
        elif DEST in self.names and self.names[DEST] not in listen_socks:
            raise ConnectionError
        else:
                LOGGER.error(
                    f'Попытка отправить сообщение на "деревню к дедушке": {DEST}')



def parse_argv():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--addr', nargs='?', default="",
                        help='Укажите адрес доступный для клиента, по умолчанию будет указан адрес ""')
    parser.add_argument('-p', '--port', nargs='?', default='7777',
                        help='Укажите номер порта сервера, по умолчанию будет указан порт 7777')
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

    try:
        if 'addr' in param_names:
            listen_address = args.addr
        else:
            raise IndexError
    except IndexError:
        LOGGER.error(
            'После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
        sys.exit(1)
    return listen_address, listen_port



def main():
    """Царь-функция"""
    listen_address, listen_port = parse_argv()
    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
