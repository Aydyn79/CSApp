import argparse
import json
import sys, os
from argparse import Namespace
import time

sys.path.append(os.path.join(os.getcwd(), '..'))

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, inet_aton
from types import TracebackType
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT


def get_addr_port(n_addr, value_addr, n_port, value_port):
    parser = argparse.ArgumentParser()
    parser.add_argument(n_addr, nargs='?', default="")
    parser.add_argument(n_port, nargs='?', default='7777')
    args = parser.parse_args([n_addr, value_addr, n_port, value_port])
    param_names = [param_name for param_name, _ in vars(args).items()]
    if 'addr' in param_names:
        address = args.addr
    elif 'a' in param_names:
        address = args.a
    else:
        address = 0
    if 'port' in param_names:
        port = int(args.port)
    elif 'p' in param_names:
        port = int(args.p)
    else:
        port = 0
    return (address, port)


# out = {
#     ACTION: PRESENCE,
#     TIME: time.time(),
#     USER: {
#         ACCOUNT_NAME: account_name
#     }
# }


def process_ans(message):
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise ValueError


def valid_ip(address):
    try:
        if inet_aton(address):
            return True
    except OSError:
        if address == 'localhost':
            return True
        else:
            return False


def get_message(client_response):
    if isinstance(client_response, bytes):
        json_response = client_response.decode('utf-8')
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        return 0
    return 0


def send_message(message):
    if not isinstance(message, dict):
        raise TypeError
    js_message = json.dumps(message)
    return js_message.encode('utf-8')

# print(send_message('message'))
