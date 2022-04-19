import argparse
import socket
import sys
import logging
import json
import threading
import time

from PyQt5.QtCore import pyqtSignal, QObject

from common.errors import ReqFieldMissingError
from client_base import ClientDatabase
from config_client_log import LOGGER
from utils import valid_ip, send_message, get_message
from variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, EXIT, MESSAGE, SENDER, DESTINATION, \
    MESSAGE_TEXT

sys.path.append('../')
from common.utils import *
from common.variables import *
from common.errors import ServerError

# переменная блокировки для работы с сокетом.
lock_sock = threading.Lock()


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
        self.connection_init(port, ip_address)
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

    def data_exchange_init(self, port, ip_address, username):
        """Сообщаем о запуске"""
        LOGGER.info(f'Запущен клиент {username} с параметрами: '
                    f'адрес сервера: {ip_address}, порт: {port}')
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Таймаут для освобождения сокета.
        transport.settimeout(5)
        for i in range(5):
            LOGGER.info(f"Моя попытка №{i}")
            try:
                transport.connect((ip_address, port))
            except (OSError,ConnectionRefusedError, ConnectionError):
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
            send_message(transport, self.create_presence(self.username))
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
        LOGGER.debug('Транспорт завершает работу.')
        time.sleep(0.5)





    # @log
    def create_message(self, to_user, message):
        """
        Функция генерации и отправки сообщения
        """
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


