"""Программа-клиент"""
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

from meta_detect import CliSupervisor
from logs.config_client_log import LOGGER




class Client_sender(threading.Thread, metaclass=CliSupervisor):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    # @log
    def create_exit_message(self):
        """Функция создаёт словарь с сообщением о выходе"""
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }


    # @log
    def create_message(self):
        """
        Функция запрашивает кому отправить сообщение и само сообщение,
        и отправляет полученные данные на сервер
        :param sock:
        :param account_name:
        :return:
        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
        except Exception as e:
            print(e)
            LOGGER.critical('Потеряно соединение с сервером.')
            sys.exit(1)

    # @log
    def run(self):
        """Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                self.send_message(self.sock, self.create_exit_message())
                print('Завершение соединения.')
                LOGGER.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    def print_help(self):
        """Функция выводящяя справку по использованию"""
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

class Client_reader(threading.Thread, metaclass=CliSupervisor):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    # @log
    def run(self):
        """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name \
                        or message[DESTINATION] == 'for_all':
                    print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                          f'\n{message[MESSAGE_TEXT]}')
                    LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                                f'\n{message[MESSAGE_TEXT]}')
                else:
                    LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
            except IncorrectDataRecivedError:
                LOGGER.error(f'Не удалось декодировать полученное сообщение.')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                LOGGER.critical(f'Потеряно соединение с сервером.')
                break


# @log
def create_presence(account_name):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return out


# @log
def process_ans(message):
    '''
    Функция разбирает ответ сервера
    :param message:
    :return:
    '''
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        # return f'400 : {message[ERROR]}'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE, message)


def getParseArgv():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-a', '--addr', nargs='?', default="127.0.0.1",
                            help='Укажите адрес доступный для клиента, по умолчанию будет указан адрес "127.0.0.1"')
        parser.add_argument('-p', '--port', nargs='?', default="7777",
                            help='Укажите номер порта сервера, по умолчанию будет указан порт 7777')
        parser.add_argument('-n', '--name', default=None, nargs='?')
        args = parser.parse_args()
        param_names = [param_name for param_name, _ in vars(args).items()]

        if 'port' in param_names:
            listen_port = int(args.port)
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except TypeError:
        LOGGER.critical(f'После параметра -\'p\' необходимо указать номер порта.')
        sys.exit(1)
    except ValueError:
        LOGGER.error(
            f'Попытка запуска клиента с неподходящим номером порта: {listen_port}.'
            f' Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    try:
        if 'addr' in param_names and args.addr is not None:
            if valid_ip(args.addr):
                listen_address = args.addr
            else:
                raise UnboundLocalError
        else:
            raise ValueError
    except ValueError:
        LOGGER.error(
            'После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
        sys.exit(1)
    except UnboundLocalError:
        LOGGER.error(
            'Неверный формат IP адреса')
        sys.exit(1)

    if 'name' in param_names and args.name is not None:
        client_name = args.name
    else:
        client_name = input('Введите имя клиента, это обязательный параметр: ')

    return listen_address, listen_port, client_name


def main():
    server_address, server_port, client_name = getParseArgv()
    """Сообщаем о запуске"""
    LOGGER.info(f'Запущен клиент {client_name} с параметрами: '
                f'адрес сервера: {server_address}, порт: {server_port}')
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_ans(get_message(transport))
        LOGGER.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        LOGGER.error('Не удалось декодировать полученную Json строку.')
        sys.exit(1)
    except ServerError as error:
        LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        sys.exit(1)
    except ReqFieldMissingError as missing_error:
        LOGGER.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        sys.exit(1)
    except (ConnectionRefusedError, ConnectionError):
        LOGGER.critical(
            f'Не удалось подключиться к серверу {server_address}:{server_port}, '
            f'конечный компьютер отверг запрос на подключение.')
        sys.exit(1)
    else:
        # Если соединение с сервером установлено корректно,
        # запускаем клиентский процесс приёма сообщений
        receiver = Client_reader(client_name, transport)
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        sender = Client_sender(client_name, transport)
        sender.daemon = True
        sender.start()
        LOGGER.debug('Запущены процессы, ой запущены')

        # Watchdog основной цикл, если один из потоков завершён,
        # то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках,
        # достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if receiver.is_alive() and sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
