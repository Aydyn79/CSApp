import sys

sys.path.append('../')

from common.variables import DEFAULT_IP_ADDRESS, DEFAULT_PORT, MAX_CONNECTIONS
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

def emulate_conn(message):# Создаем тестовый сокет для сервера
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind((DEFAULT_IP_ADDRESS, DEFAULT_PORT))
    server_socket.listen(MAX_CONNECTIONS)

    # Создаем тестовый сокет для клиента
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((DEFAULT_IP_ADDRESS, DEFAULT_PORT))

    # Отправляем и получаем сообщение
    client, address = server_socket.accept()
    msg = message.encode('utf-8')
    client_socket.send(msg)
    answer = client.recv(1024)
    return answer.decode('utf-8')

# print(emulate_conn('Привет лунатикам'))
