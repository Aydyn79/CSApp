"""Программа-клиент"""
import argparse
import logging
import sys
import json
import socket
import threading
import time
from client_base import ClientDatabase
from server_base import Server_db
from errors import *
from common.variables import *
from common.utils import *
from meta_detect import CliSupervisor
from logs.config_client_log import LOGGER

lock_socket = threading.Lock()
lock_db = threading.Lock()


class Client_sender(threading.Thread, metaclass=CliSupervisor):
    def __init__(self, account_name, sock, db):
        self.account_name = account_name
        self.sock = sock
        self.db = db
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
        if not self.db.check_user(to_user):
            LOGGER.error(f'Попытка отправить сообщение незарегистрированному пользователю {to_user}')
            return
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')

        with lock_db:
            self.db.save_message(self.account_name, to_user, message)

        with lock_socket:
            try:
                send_message(self.sock, message_dict)
                LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
            except OSError as e:
                if e.errno:
                    print(e)
                    LOGGER.critical('Потеряно соединение с сервером.')
                    sys.exit(1)
                else:
                    LOGGER.critical('Не удалось установить соединение с сервером, таймаут соединения')

    # @log
    def run(self):
        """Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'mess':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                with lock_socket:
                    try:
                        print('Завершение соединения.')
                        LOGGER.info('Завершение работы по команде пользователя.')
                        send_message(self.sock, self.create_exit_message())
                    except:
                        pass
                    LOGGER.info('Завершение работы пользователя')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            # Вызов списка активных пользователей
            elif command == 'cont':
                with lock_db:
                    contacts_list = self.db.get_contacts()
                for contact in contacts_list:
                    print(contact)

            # elif command == 'actv':
            #     with lock_db:
            #         # если список пуст, так и пишем
            #         if not Server_db.active_users_list(self.account_name):
            #             print('Вы один активный, остальные все пассивные')
            #         else:
            #             # если есть активные пользователи кроме самого клиента, выводим их список
            #             for user in sorted(Server_db.active_users_list(self.account_name)):
            #                 print(
            #                     f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, время установки соединения: {user[3]}')

            # Редактирование контактов
            elif command == 'edit':
                self.edit_contacts()

            # история сообщений.
            elif command == 'hist':
                self.print_history()

            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    def print_help(self):
        """Функция выводящяя справку по использованию"""
        print('Поддерживаемые команды:')
        print('mess - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('edit - редактировать список контактов')
        print('cont - вывести список контактов')
        print('actv - вывести список активных пользователей (запрос с сервера)')
        print('hist - вывести историю сообщений')
        print('exit - выход из программы')

    def print_history(self):
        direction = input('in - входящие, out - исходящие, все - нажать Enter: ')
        with lock_db:
            if direction == 'in':
                history_list = self.db.get_history(to_who=self.account_name)
                for msg in history_list:
                    print(f'\nСообщение от пользователя: {msg[0]} к {msg[3]}:\n{msg[2]}')
            elif direction == 'out':
                history_list = self.db.get_history(from_who=self.account_name)
                for msg in history_list:
                    print(f'\nСообщение для пользователя: {msg[0]} {msg[1]} от {msg[3]}:\n{msg[2]}')
            else:
                history_list = self.db.get_history()
                for msg in history_list:
                    print(f'\nСообщение от пользователя: {msg[0]}, пользователю {msg[1]} от {msg[3]}\n{msg[2]}')

    def edit_contacts(self):
        act = input('Чтобы удалить контакт - введите del, чтобы добавить - введите add: ')
        if act == 'del':
            edit = input('Введите имя контакта: ')
            with lock_db:
                if self.db.check_contact(edit):
                    self.db.del_contact(edit)
                    LOGGER.info('Указанный Вами контакт удален.')
                else:
                    LOGGER.error('Указанный Вами контакт не существует.')
        elif act == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя: ')
            if self.db.check_user(edit):
                with lock_db:
                    self.db.add_contact(edit)
                with lock_socket:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except ServerError:
                        LOGGER.error('Не удалось отправить информацию на сервер.')


# class Client_reader(threading.Thread, metaclass=CliSupervisor):
class Client_reader(threading.Thread):
    def __init__(self, account_name, sock, db):
        self.account_name = account_name
        self.sock = sock
        self.db = db
        super().__init__()

    # @log
    def run(self):
        """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
        while True:
            time.sleep(1)
            with lock_socket:
                try:
                    message = get_message(self.sock)
                except IncorrectDataRecivedError:
                    LOGGER.error(f'Не удалось декодировать полученное сообщение.')
                except (OSError, ConnectionError, ConnectionAbortedError,
                        ConnectionResetError, json.JSONDecodeError):
                    LOGGER.critical(f'Потеряно соединение с сервером.')
                    # break
                    pass
                else:
                    if ACTION in message and message[ACTION] == MESSAGE \
                            and SENDER in message \
                            and DESTINATION in message \
                            and MESSAGE_TEXT in message \
                            and message[DESTINATION] == self.account_name \
                            or message[DESTINATION] == 'for_all':
                        print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                              f'\n{message[MESSAGE_TEXT]}')
                        # LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                        #         f'\n{message[MESSAGE_TEXT]}')
                        with lock_db:
                            try:
                                self.db.save_message(message[SENDER],
                                                 self.account_name,
                                                 message[MESSAGE_TEXT])
                            except Exception as e:
                                print(e)
                                LOGGER.error('Ошибка взаимодействия с базой данных')

                        LOGGER.info(f'Получено сообщение от пользователя '
                                    f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    else:
                        LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')


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


# Функция запрос контакт листа
def contacts_list_request(sock, name):
    LOGGER.debug(f'Запрос контакт-листа для пользователя {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    LOGGER.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = get_message(sock)
    LOGGER.debug(f'Получен ответ {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


# Функция добавления пользователя в контакт лист
def add_contact(sock, username, contact):
    LOGGER.debug(f'Создание контакта {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')


# Функция запроса списка известных пользователей
def user_list_request(sock, username):
    LOGGER.debug(f'Запрос списка известных пользователей {username}')
    req = {
        ACTION: USER_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


# Функция удаления пользователя из списка контактов
def remove_contact(sock, username, contact):
    LOGGER.info(f'Удаление контакта {contact}')
    req = {
        ACTION: DEL_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        LOGGER.info(f'Контакт {contact} удалён')
    else:
        raise ServerError('Ошибка удаления контакта')


# Загрузка данных в базу данных клиента с базы данных сервера.
def database_load(sock, db, username):
    # Загружаем список известных пользователей
    try:
        all_users = user_list_request(sock, username)
    except ServerError:
        LOGGER.error('Ошибка запроса списка известных пользователей.')
    else:
        db.add_users(all_users)

    # Загружаем список контактов
    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        LOGGER.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            db.add_contact(contact)


def main():
    server_address, server_port, client_name = getParseArgv()
    """Сообщаем о запуске"""
    LOGGER.info(f'Запущен клиент {client_name} с параметрами: '
                f'адрес сервера: {server_address}, порт: {server_port}')
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Таймаут для освобождения сокета.
        transport.settimeout(1)
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
        db = ClientDatabase(client_name)
        database_load(transport, db, client_name)

        # Если соединение с сервером установлено корректно,
        # запускаем клиентский процесс приёма сообщений
        receiver = Client_reader(client_name, transport, db)
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        sender = Client_sender(client_name, transport, db)
        sender.daemon = True
        sender.start()
        LOGGER.debug('Запущены процессы')

        # Watchdog основной цикл, если один из потоков завершён,
        # то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках,
        # достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if receiver.is_alive() and sender.is_alive():
            # if sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
