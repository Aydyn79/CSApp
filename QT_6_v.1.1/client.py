"""Программа-клиент"""
import argparse
import os

from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox
from client.main_window import ClientMainWindow
from client.net_client import NetClient
from client.start_dialog import UserNameDialog
from client.client_base import ClientDatabase
from common.errors import *
from common.utils import *
from logs.config_client_log import LOGGER



def getParseArgv():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-a', '--addr', nargs='?', default="127.0.0.1",
                            help='Укажите адрес доступный для клиента, по умолчанию будет указан адрес "127.0.0.1"')
        parser.add_argument('-p', '--port', nargs='?', default="7777",
                            help='Укажите номер порта сервера, по умолчанию будет указан порт 7777')
        parser.add_argument('-n', '--name', default=None, nargs='?')
        parser.add_argument('--password', default='', nargs='?')
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

    client_name = args.name
    client_passwrd = args.password
    return listen_address, listen_port, client_name, client_passwrd


def main():
    server_address, server_port, client_name, client_passwrd = getParseArgv()
    # Создаём клиентокое приложение
    client_app = QApplication(sys.argv)

    # Если имя пользователя или пароль не было указаны в командной строке, то запрашиваем их
    if not client_name or not client_passwrd:
        start_dialog = UserNameDialog()
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            LOGGER.info(f'Используется имя пользователя: {client_name}, пароль из стартовой формы: {client_passwd}')
            # del start_dialog
        else:
            exit(0)

    LOGGER.info(f'Запущен клиент {client_name} с параметрами: '
                f'адрес сервера: {server_address}, порт: {server_port}')

    # Загружаем ключи с файла, если же файла нет, то генерируем новую пару.
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    LOGGER.info('Паспорту, ключи загружены!')

    # Создаём объект базы данных
    db = ClientDatabase(client_name)

    try:
        transport = NetClient(
            server_port,
            server_address,
            db,
            client_name,
            client_passwd,
            keys)
        LOGGER.info('Транспорт готов Коммандор!')
    except ServerError as error:
        LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', error.text)
        sys.exit(1)
    else:
        transport.setDaemon(True)
        transport.start()

        del start_dialog
        # Создаём GUI
        main_window = ClientMainWindow(db, transport, keys)
        main_window.make_connection(transport)
        main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
        client_app.exec_()

        # Раз графическая оболочка закрылась, закрываем транспорт
        transport.exit_chat()
        transport.join()


if __name__ == '__main__':
    main()
