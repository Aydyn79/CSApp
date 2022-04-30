import argparse
import sys,os, unittest
import socket
sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE, \
    DEFAULT_IP_ADDRESS
from client import *

class ParseArgvClient:
    '''Модель части кода файла client_app.py, отвечающего за парсинг параметров
    командной строки и возвращающего значения порта и IP адреса'''
    def __init__(self, n_addr, value_addr, n_port, value_port):
        self.n_addr = n_addr
        self.value_addr = value_addr
        self.n_port = n_port
        self.value_port = value_port

    def get_addr_port(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(self.n_addr, nargs='?', default="127.27.10.1")
        parser.add_argument(self.n_port, nargs='?', default='7777')
        args = parser.parse_args([self.n_addr, self.value_addr, self.n_port, self.value_port])
        param_names = [param_name for param_name, _ in vars(args).items()]
        try:
            if 'port' in param_names:
                listen_port = int(args.port)
            elif 'p' in param_names:
                listen_port = int(args.p)
            if listen_port < 1024 or listen_port > 65535:
                raise ValueError
        except TypeError:
            print('После параметра -\'p\' необходимо указать номер порта.')
            sys.exit(1)
        except ValueError:
            print('В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
            sys.exit(1)
        try:
            if 'addr' in param_names:
                listen_address = args.addr
            elif 'a' in param_names:
                listen_address = args.a
        except IndexError:
            print('После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
            sys.exit(1)
        return listen_address, listen_port

def emulate_conn(message):# тестовый сокет для клиента и сервера
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((DEFAULT_IP_ADDRESS, DEFAULT_PORT))
    server_socket.listen(MAX_CONNECTIONS)

    # Создаем тестовый сокет для клиента
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((DEFAULT_IP_ADDRESS, DEFAULT_PORT))

    # Отправляем и получаем сообщение
    client, address = server_socket.accept()
    msg = message.encode('utf-8')
    client_socket.send(msg)
    answer = client.recv(1024)
    client.close()
    client_socket.close()
    server_socket.close()
    return answer.decode('utf-8')


class TestClient(unittest.TestCase):
    default_addr_client = '127.0.0.1'
    port = '7777'
    result_client = ('127.0.0.1', 7777)
    IP_wrong = '9999.9999.0.1'
    IP_valid = '127.0.0.1'
    msg_correct = {"IP":"127.0.0.1","port":"8888"}
    msg_wrong = ['IP', "127.0.0.1", "port", "8888"]
    response200 = {RESPONSE: 200}
    response400 = {RESPONSE: 400, ERROR: 'Bad Request'}
    message = {ACTION: 200}
    tMsg = 'Привет'

    def SetUp(self):
        pass

    def tearDown(self):
        pass

    def testGetAddrPortClnt(self):
        '''Тестирование корректности считывания параметров IP адреса и номера порта из командной строки для клиента'''
        getAddrPort = ParseArgvClient('-a',self.default_addr_client,'-p',self.port)
        self.assertEqual(getAddrPort.get_addr_port(), self.result_client)

    def testIPValid(self):
        '''Тестирование функции valid_ip при правильном формате IP адреса'''
        self.assertTrue(valid_ip(self.IP_valid))

    def testIPWrong(self):
        '''Тестирование функции valid_ip при неправильном формате IP адреса'''
        self.assertFalse(valid_ip(self.IP_wrong))

    def testEmulateConn(self):
        '''Тестирование соединения между клиентом и сервером, шифровки и дешифровки сообщения.
         В качестве критерия успешности - корректный ответ от сервера'''
        self.assertEqual(emulate_conn(self.tMsg), self.tMsg)

    def testProcessAns200(self):
        self.assertEqual(process_ans(self.response200), '200 : OK')

    def testProcessAns400(self):
        self.assertEqual(process_ans(self.response400), '400 : Bad Request')

    def testProcessAnsExc(self):
        '''Тестирование возникновения исключения ValueError в функции process_ans
        возникающее при некорректном формате сообщения'''
        self.assertRaises(ValueError,process_ans, self.message)

    def testPresense(self):
        presense = create_presence()
        presense[TIME] = 2
        self.assertEqual(presense, {ACTION: PRESENCE, TIME: 2, USER: {ACCOUNT_NAME: 'Guest'}})

if __name__ == '__main__':
    unittest.main()
