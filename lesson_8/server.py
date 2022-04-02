"""Программа-сервер"""
import argparse
import select
import socket
import sys
from datetime import time
from threading import Thread

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE, RESPONSE_400, RESPONSE_200, DESTINATION, \
    MESSAGE, MESSAGE_TEXT, SENDER, EXIT
from common.utils import get_message, send_message
from logs.config_server_log import LOGGER


def process_client_message(message, messages_list, client, clients, names):
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
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = client
            send_message(client, RESPONSE_200)
        else:
            response = RESPONSE_400
            response[ERROR] = 'Имя пользователя уже занято.'
            LOGGER.info(f'Попытка войти в чат под существующим именем \
                {message[USER][ACCOUNT_NAME]}')
            send_message(client, response)
            clients.remove(client)
            client.close()
        return
    elif ACTION in message and message[ACTION] == MESSAGE and \
            DESTINATION in message and TIME in message \
            and SENDER in message and MESSAGE_TEXT in message:
        LOGGER.info(f'Клиент {message[SENDER]} прислал сообщение {message[MESSAGE_TEXT]} пользователю {message[DESTINATION]}') #Тайна переписки? Неа, не слышал)
        messages_list.append(message)
        return
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        clients.remove(names[message[ACCOUNT_NAME]])
        names[message[ACCOUNT_NAME]].close()
        del names[message[ACCOUNT_NAME]]
        return
    else:
        LOGGER.error(f'Сообщение от клиента {message} не прошло валидацию')
        response = RESPONSE_400
        response[ERROR] = 'Запрос некорректен.'
        send_message(client, response)
        return

# def process_message(message, names, listen_socks):
#     if isinstance(message[DESTINATION],str):
#         DEST = message[DESTINATION]
#         if DEST in names and names[DEST] in listen_socks:
#             send_message(names[DEST], message)
#             LOGGER.info(f'Отправлено сообщение пользователю {DEST} '
#                         f'от пользователя {message[SENDER]}.')
#         elif DEST in names and names[DEST] not in listen_socks:
#             raise ConnectionError
#         else:
#             LOGGER.error(
#                 f'Попытка отправить сообщение на "деревню к дедушке": {DEST}')
#     elif isinstance(message[DESTINATION],tuple):
#         recipients = message[DESTINATION]
#         for item in recipients:
#             if item in names and names[item] in listen_socks:
#                 send_message(names[item], message)
#                 LOGGER.info(f'Отправлено сообщение пользователю {item} '
#                             f'от пользователя {message[SENDER]}.')
#             elif item in names and names[item] not in listen_socks:
#                 raise ConnectionError
#             else:
#                 LOGGER.error(
#                     f'Попытка отправить сообщение на "деревню к дедушке": {item}')
#     else:
#         raise TypeError

def process_message(message, names, listen_socks):
    DEST = message[DESTINATION]
    if DEST in names and names[DEST] in listen_socks:
        send_message(names[DEST], message)
        LOGGER.info(f'Отправлено сообщение пользователю {DEST} '
                        f'от пользователя {message[SENDER]}.')
    elif DEST in names and names[DEST] not in listen_socks:
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

    # Готовим сокет
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    transport.bind((listen_address, listen_port))
    transport.settimeout(0.2)

    # список клиентов , очередь сообщений
    clients = []
    messages = []

    # Словарь, содержащий имена пользователей и соответствующие им сокеты.
    names = dict()  # {client_name: client_socket}

    # Слушаем порт
    transport.listen(MAX_CONNECTIONS)
    # Основной цикл программы сервера
    while True:
        try:
            client, client_address = transport.accept()
        except OSError:
            LOGGER.info(f'Cоединение не установлено, время для подключения истекло')
            pass
        else:
            LOGGER.info(f'Установлено соединение с клиентом: {client_address}')
            clients.append(client)

        recv_data_lst = []
        send_data_lst = []
        # сбор клиентов на чтение или запись

        try:
            if clients:
                recv_data_lst, send_data_lst, _ = select.select(clients, clients, [], 0)
        except OSError:
            pass

        # принимаем сообщения и если ошибка, исключаем клиента.
        if recv_data_lst:
            for client_with_message in recv_data_lst:
                try:
                    process_client_message(get_message(client_with_message),
                                           messages, client_with_message, clients, names)
                except Exception:
                    LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                f'отключился от сервера.')
                    clients.remove(client_with_message)
        # Если есть сообщения, обрабатываем каждое.
        for i in messages:
            try:
                # Обработка широковещательных сообщений
                # if i[DESTINATION] == 'for_all' and isinstance(i[DESTINATION],str):
                if i[DESTINATION] == 'for_all':
                    for cli in clients:
                        send_message(cli, i)
                # Обработка сообщения точка-точка.
                else:
                    process_message(i, names, send_data_lst)
                # Это пока что неудачная попытка сделать рассылку сообщения нескольким клиентам, но не всем
                # на досуге надо будет продолжить
                # elif isinstance(i[DESTINATION],list):
                #     for z in i[DESTINATION]:
                #         if z in names.keys():
                #             process_message(z, names, send_data_lst)
                #         else:
                #             continue
            except Exception:
                LOGGER.info(f'Связь с клиентом с именем {i[DESTINATION]} была потеряна')
                clients.remove(names[i[DESTINATION]])
                del names[i[DESTINATION]]

        messages.clear()



if __name__ == '__main__':
    main()
