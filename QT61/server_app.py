"""Программа-сервер"""
import argparse
import configparser
import os
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
sys.path.append('../')
from common.variables import DEFAULT_PORT
from logs.config_server_log import LOGGER
from server.server_base import Server_db
from server.msg_processor import MessageProcessor
from server.main_window import MainWindow



# Флаг, что был подключён новый пользователь, нужен чтобы не мучать BD
# постоянными запросами на обновление

def parse_argv(default_port, default_address):

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--addr', nargs='?', default=default_address,
                        help='Укажите адрес доступный для клиента, по умолчанию будет указан адрес ""')
    parser.add_argument('-p', '--port', nargs='?', default=default_port,
                        help='Укажите номер порта сервера, по умолчанию будет указан порт 7777')
    parser.add_argument('--no_gui', action='store_true')
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
    # Времени мало, не стал проверку делать
    gui_flag = args.no_gui
    return listen_address, listen_port, gui_flag


def config_load():
    '''
    Загрузка параметров конфигурации
    '''
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    # Если конфиг файл загружен правильно, запускаемся, иначе конфиг по умолчанию.
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_base.db3')
        return config


def main():
    """Царь-функция"""
    config = config_load()

    listen_address, listen_port, gui_flag = parse_argv(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    database = Server_db(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))

    # Создание экземпляра класса - сервера и его запуск:
    server = MessageProcessor(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    if gui_flag:
        while True:
            command = input('Введите exit для завершения работы сервера.')
            if command == 'exit':
                # Если выход, то завершаем основной цикл сервера.
                server.running = False
                server.join()
                break

        # Если не указан запуск без GUI, то запускаем GUI:
    else:
        # Создаём графическое окружение для сервера:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)

        # Запускаем GUI
        server_app.exec_()

        # По закрытию окон останавливаем обработчик сообщений
        server.running = False


if __name__ == '__main__':
    main()