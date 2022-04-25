import binascii
import hmac
import os
import select
import socket
import sys
import threading

sys.path.append('../')
from common.variables import RESPONSE_511, DATA, PUBLIC_KEY, RESPONSE_205, REMOVE_CONTACT, USERS_REQUEST, PUBLIC_KEY_REQUEST,\
    ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, RESPONDEFAULT_IP_ADDRESSSE, RESPONSE_400,\
    RESPONSE_200, DESTINATION, MESSAGE, MESSAGE_TEXT, SENDER, EXIT, GET_CONTACTS, LIST_INFO, ADD_CONTACT, DEL_CONTACT, \
    USER_REQUEST, RESPONSE_202, DEFAULT_PORT
from meta_detect import ServSupervisor
from descript import Port, Address
from common.utils import get_message, send_message
from logs.config_server_log import LOGGER




# Флаг, что был подключён новый пользователь, нужен чтобы не мучать BD
# постоянными запросами на обновление
# new_connection = False
# conflag_lock = threading.Lock()


class MessageProcessor(threading.Thread, metaclass=ServSupervisor):
    """
    Класс-обработчик входящих соединений и
    сообщений, запускается в отдельном потоке.
    """
    port = Port()
    addr = Address()

    def __init__(self, listen_address, listen_port, db):
        # Параметры подключения
        self.addr = listen_address
        self.port = listen_port

        # Список подключённых клиентов.
        self.clients = []

        # Сокет, через который будет осуществляться работа
        self.sock = None

        # Сокеты
        self.listen_sockets = None
        self.error_sockets = None

        # Флаг продолжения работы
        self.running = True

        # БД сервера
        self.db = db

        # Словарь содержащий сопоставленные имена и соответствующие им сокеты.
        self.names = dict()

        # Конструктор предка
        super().__init__()

    def init_socket(self):
        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # transport = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)
        # Слушаем порт
        self.sock = transport
        self.sock.listen(5)

    def run(self):
        """
        Основной метод потока
        Осуществляет обработку входящих соединений,
        сообщений, отвечает за авторизацию пользователей
        """
        self.init_socket()

        # Основной цикл программы сервера
        while self.running:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                LOGGER.info(f'Cоединение не установлено, время для подключения истекло')
                pass
            else:
                LOGGER.info(f'Установлено соединение с клиентом: {client_address}')
                # client.settimeout(5)
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # сбор клиентов на чтение или запись

            try:
                if self.clients:
                    recv_data_lst, self.listen_sockets, self.error_sockets = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as err:
                LOGGER.error(f'Ошибка работы с сокетами: {err.errno}')

            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(
                            get_message(client_with_message), client_with_message)
                    except Exception:
                        LOGGER.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        self.client_remove(client_with_message)
                        with conflag_lock:
                            new_connection = True

    def client_remove(self, client):
        '''
        Метод обработчик клиента с которым прервана связь.
        Ищет клиента и удаляет его из списков и базы:
        '''
        LOGGER.info(f'Клиент {client.getpeername()} отключился от сервера.')
        for name in self.names:
            if self.names[name] == client:
                self.db.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    @login_required
    def process_client_message(self, message, client):
        '''
        Обработчик сообщений от клиентов, принимает словарь -
        сообщение от клиента, проверяет корректность,
        возвращает словарь-ответ для клиента
        '''
        LOGGER.debug('Анализ входящего сообщения')
        if ACTION in message \
                and message[ACTION] == PRESENCE \
                and TIME in message \
                and USER in message:
            LOGGER.info('Сообщение от клиента прошло валидацию')
            LOGGER.info('Запускаю процедуру авторизации')
            self.autorize_user(message, client)
            # Если это сообщение, то отправляем его получателю.
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and DESTINATION in message \
                and TIME in message \
                and SENDER in message \
                and MESSAGE_TEXT in message \
                and self.names[message[SENDER]] == client:
            if message[DESTINATION] in self.names:
                self.db.process_message(
                    message[SENDER], message[DESTINATION])
                self.process_message(message)
                try:
                    send_message(client, RESPONSE_200)
                except OSError:
                    self.client_remove(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Пользователь не зарегистрирован на сервере.'
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return

        # Если клиент выходит
        elif ACTION in message \
                and message[ACTION] == EXIT \
                and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            self.client_remove(client)

        # Если это запрос контакт-листа
        elif ACTION in message \
                and message[ACTION] == GET_CONTACTS \
                and USER in message \
                and self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.db.get_contacts(message[USER])
            try:
                send_message(client, response)
            except OSError:
                self.client_remove(client)

        # Если это добавление контакта
        elif ACTION in message \
                and message[ACTION] == ADD_CONTACT \
                and ACCOUNT_NAME in message \
                and USER in message \
                and self.names[message[USER]] == client:
            self.db.add_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.client_remove(client)

        # Если это удаление контакта
        elif ACTION in message \
                and message[ACTION] == REMOVE_CONTACT \
                and ACCOUNT_NAME in message \
                and USER in message \
                and self.names[message[USER]] == client:
            self.db.remove_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.client_remove(client)

        # Если это запрос известных пользователей
        elif ACTION in message \
                and message[ACTION] == USERS_REQUEST \
                and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.db.users_list()]
            try:
                send_message(client, response)
            except OSError:
                self.client_remove(client)

        # Если это запрос публичного ключа пользователя
        elif ACTION in message \
                and message[ACTION] == PUBLIC_KEY_REQUEST \
                and ACCOUNT_NAME in message:
            response = RESPONSE_511
            response[DATA] = self.db.get_pubkey(message[ACCOUNT_NAME])
            # может быть, что ключа ещё нет (пользователь никогда не логинился,
            # тогда шлём 400)
            if response[DATA]:
                try:
                    send_message(client, response)
                except OSError:
                    self.client_remove(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Нет публичного ключа для данного пользователя'
                try:
                    send_message(client, response)
                except OSError:
                    self.client_remove(client)

        else:
            response = RESPONSE_400
            response[ERROR] = 'Некорректный запрос'
            LOGGER.info(f'Некорректный формат сообщения')
            send_message(client, response)
            self.client_remove(client)
        return

    def autorize_user(self, message, sock):
        """ Метод реализующий авторизацию пользователей. """
        # Если имя пользователя уже занято то возвращаем 400
        LOGGER.debug(f'Start auth process for {message[USER]}')
        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = RESPONSE_400
            response[ERROR] = 'Имя пользователя уже занято.'
            try:
                LOGGER.debug(f'Username busy, sending {response}')
                send_message(sock, response)
            except OSError:
                LOGGER.debug('OS Error')
                pass
            self.clients.remove(sock) #???? was ist das
            sock.close()
        # Проверяем что пользователь зарегистрирован на сервере.
        elif not self.db.check_user(message[USER][ACCOUNT_NAME]):
            response = RESPONSE_400
            response[ERROR] = 'Пользователь не зарегистрирован.'
            try:
                LOGGER.debug(f'Unknown username, sending {response}')
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            LOGGER.debug('Correct username, starting passwd check.')
            # Иначе отвечаем 511 и проводим процедуру авторизации
            # Словарь - заготовка
            message_auth = RESPONSE_511
            # Набор байтов в hex представлении
            random_str = binascii.hexlify(os.urandom(64))
            # В словарь байты нельзя, декодируем (json.dumps -> TypeError)
            message_auth[DATA] = random_str.decode('ascii')
            # Создаём хэш пароля и связки с рандомной строкой, сохраняем
            # серверную версию ключа
            hash = hmac.new(self.db.get_hash(message[USER][ACCOUNT_NAME]), random_str, 'MD5')
            digest = hash.digest()
            LOGGER.debug(f'Auth message = {message_auth}')
            try:
                # Обмен с клиентом
                send_message(sock, message_auth)
                ans = get_message(sock)
            except OSError as err:
                LOGGER.debug('Error in auth, data:', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[DATA])
            # Если ответ клиента корректный, то сохраняем его в список
            # пользователей.
            if RESPONSE in ans and ans[RESPONSE] == 511 and \
                    hmac.compare_digest(digest, client_digest):
                self.names[message[USER][ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, RESPONSE_200)
                except OSError:
                    self.client_remove(message[USER][ACCOUNT_NAME])
                # добавляем пользователя в список активных и,
                # если у него изменился открытый ключ, то сохраняем новый
                self.db.user_login(
                    message[USER][ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[USER][PUBLIC_KEY])
            else:
                response = RESPONSE_400
                response[ERROR] = 'Неверный пароль.'
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def process_message(self, message, listen_socks):
        '''
        Метод-передаст.
        '''
        DEST = message[DESTINATION]
        if DEST in self.names \
                and self.names[DEST] in listen_socks:
            try:
                send_message(self.names[DEST], message)
                LOGGER.info(f'Отправлено сообщение пользователю {DEST} '
                            f'от пользователя {message[SENDER]}.')
            except OSError:
                self.client_remove(DEST)
                LOGGER.info("Упс, что-то пошло не так")
        elif DEST in self.names \
                and self.names[DEST] not in listen_socks:
            LOGGER.error(f'Связь с клиентом {message[DESTINATION]} потеряна.')
        else:
            LOGGER.error(f'Попытка отправить сообщение на "деревню к дедушке": {DEST}')

    def service_update_lists(self):
        '''Метод реализующий отправки сервисного сообщения 205 клиентам.'''
        for client in self.names:
            try:
                send_message(self.names[client], RESPONSE_205)
            except OSError:
                self.client_remove(self.names[client])
