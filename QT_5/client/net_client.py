import argparse
import socket
import sys
import logging
import json
import threading
import time

from PyQt5.QtCore import pyqtSignal, QObject

sys.path.append('../')
from common.errors import ReqFieldMissingError
from client_base import ClientDatabase
from logs.config_client_log import LOGGER
from common.utils import valid_ip, send_message, get_message
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, EXIT, MESSAGE, SENDER, DESTINATION, \
    MESSAGE_TEXT, GET_CONTACTS, LIST_INFO, ADD_CONTACT, USER_REQUEST, REMOVE_CONTACT
from common.errors import ServerError

# переменная блокировки для работы с сокетом.
lock_sock = threading.Lock()
lock_db = threading.Lock()

# Класс - Транспорт, отвечает за взаимодействие с сервером
class NetClient(threading.Thread, QObject):
    # Сигналы новое сообщение и потеря соединения
    new_msg = pyqtSignal(str)
    conn_lost = pyqtSignal()

    def __init__(self, port, ip_address, db, username):
        # Вызываем конструктор предка
        threading.Thread.__init__(self)
        QObject.__init__(self)

        # Класс База данных - работа с базой
        self.db = db
        # Имя пользователя
        self.username = username
        # Сокет для работы с сервером
        self.transport = None
        # Устанавливаем соединение:
        self.data_exchange_init(port, ip_address)
        # Обновляем таблицы известных пользователей и контактов
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as e:
            if e.errno:
                LOGGER.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            LOGGER.error('Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            LOGGER.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')
            # Флаг продолжения работы транспорта.
        self.running = True

    def data_exchange_init(self, port, ip_address):
        """Сообщаем о запуске"""
        LOGGER.info(f'Запущен клиент {self.username} с параметрами: '
                    f'адрес сервера: {ip_address}, порт: {port}')
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Таймаут для освобождения сокета.
        self.transport.settimeout(5)
        for i in range(5):
            LOGGER.info(f"Моя попытка №{i}")
            try:
                self.transport.connect((ip_address, port))
            except (OSError, ConnectionRefusedError, ConnectionError):
                LOGGER.info(f"Моя попытка №{i} не удалась")
                pass
            else:
                connection = True
                break
            time.sleep(1)

        if not connection:
            LOGGER.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')
        LOGGER.debug('Установлено соединение с сервером')

        # Посылаем серверу приветственное сообщение и получаем ответ,
        # что всё нормально или ловим исключение.
        try:
            send_message(self.transport, self.create_presence(self.username))
            answer = self.process_ans(get_message(self.transport))
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

    def create_presence(self, account_name):
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }
        LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
        return out

    def process_ans(self, message):
        '''
        Функция разбирает ответ сервера
        :param message:
        :return:
        '''
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            elif message[RESPONSE] == 400:
                raise ServerError(f'400 : {message[ERROR]}')
            else:
                LOGGER.error(f'Принято сообщение с неизвестным кодом: {message[RESPONSE]}')

        # Если это сообщение от пользователя добавляем в базу, даём сигнал о новом сообщении
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and SENDER in message \
                and DESTINATION in message \
                and MESSAGE_TEXT in message \
                and message[DESTINATION] == self.username:
            LOGGER.debug(f'Получено сообщение от пользователя {message[SENDER]}:'
                         f'{message[MESSAGE_TEXT]}')
            self.db.save_message(message[SENDER], 'in', message[MESSAGE_TEXT])
            self.new_msg.emit(message[SENDER])

        # Функция, обновляющая контакт - лист с сервера

    def contacts_list_update(self):
        LOGGER.debug(f'Запрос контакт листа для пользователя {self.name}')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username
        }
        LOGGER.debug(f'Сформирован запрос {req}')
        with lock_sock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        LOGGER.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST_INFO]:
                self.db.add_contact(contact)
        else:
            LOGGER.error('Не удалось обновить список контактов.')

    # Функция обновления таблицы известных пользователей.
    def user_list_update(self):
        LOGGER.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            ACTION: USER_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with lock_sock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.db.add_users(ans[LIST_INFO])
        else:
            LOGGER.error('Не удалось обновить список известных пользователей.')

    # Функция сообщающая на сервер о добавлении нового контакта
    def add_contact(self, contact):
        LOGGER.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with lock_sock:
            send_message(self.transport, req)
            self.process_ans(get_message(self.transport))

    # Функция удаления клиента на сервере
    def remove_contact(self, contact):
        LOGGER.debug(f'Удаление контакта {contact}')
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with lock_sock:
            send_message(self.transport, req)
            self.process_ans(get_message(self.transport))

    def exit_chat(self):
        """Функция выставляет флаг running в false и посылает на сервер
           словарь с сообщением о выходе
            """
        mess = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with lock_sock:
            try:
                send_message(self.transport, mess)
            except OSError:
                pass
        LOGGER.debug('Клиент завершает работу.')
        time.sleep(0.5)

    # @log
    def create_message(self, to_user, message):
        """
        Функция генерации и отправки сообщения
        """
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')

        with lock_db:
            self.db.save_message(self.username, to_user, message)

        with lock_sock:
            try:
                send_message(self.transport, message_dict)
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
        LOGGER.info('Запущен приём сообщений с сервера.')
        while self.running:
            time.sleep(1)
            with lock_sock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        LOGGER.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError,
                        ConnectionResetError, json.JSONDecodeError, TypeError):
                    LOGGER.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                # Если сообщение получено, то вызываем функцию обработчик:
                else:
                    LOGGER.debug(f'Принято сообщение с сервера: {message}')
                    self.process_ans(message)
                finally:
                    self.transport.settimeout(5)



