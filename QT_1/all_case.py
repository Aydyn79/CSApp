# Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться
# доступность сетевых узлов. Аргументом функции является список, в котором каждый
# сетевой узел должен быть представлен именем хоста или ip-адресом. В функции необходимо
# перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
# («Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен
# создаваться с помощью функции ip_address().
import ipaddress
import locale
import os
import subprocess
from ipaddress import ip_address
from pprint import pprint
from subprocess import Popen, PIPE
import platform
import locale
from tabulate import tabulate

IPs = ['45.82.153.76', 'yandex.ru', '5.255.255.60', '66.254.114.41', '5.8.223.255', '5.16.0.0', '140.82.121.3']

def host_ping(args):
    for arg in args:
        param = "-n" if platform.system().lower() == 'windows' else "-c"
        command = ["ping", param, "1", arg]
        with open(os.devnull, 'w') as Dave_Null:
            # Все системные сообщения в "битовое ведро" (os.devnull), оставляем только результаты print
            print(f'Узел {arg} доступен') if subprocess.call(command, stdout=Dave_Null) == 0 else print(f'Узел {arg} недоступен')

def host_ping1(args):
    reachable = []
    unreachable = []
    # Вариант с разбором системного сообщения
    # Кстати намного шустрее первого метода
    for arg in args:
        result = subprocess.Popen(["/bin/ping", "-c1", "-w1", arg], stdout=subprocess.PIPE).stdout.read()
        out = result.decode(locale.getpreferredencoding()).split(',')[2]
        print(f'Узел {arg} недоступен') if out == ' 100% packet loss' else print(f'Узел {arg} доступен')
        if out == ' 100% packet loss':
            unreachable.append((arg,))
        else:
            reachable.append((arg,))
    return reachable, unreachable
'''
2. Написать функцию host_range_ping() (возможности которой основаны на функции из примера 1)
для перебора ip-адресов из заданного диапазона. Меняться должен только последний октет
каждого адреса. По результатам проверки должно выводиться соответствующее сообщение.
'''
def host_range_ping(net):
    try:
        hosts = list(map(str, ipaddress.ip_network(net).hosts()))
    except ValueError as e:
        print(e)
    else:
        for host in host_ping1(hosts)[0]:
            pprint(f'Узел {host} доступен')
        print()
        for host in host_ping1(hosts)[1]:
            pprint(f'Узел {host} недоступен')

'''
3. Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2.
Но в данном случае результат должен быть итоговым по всем ip-адресам, представленным в табличном формате
(использовать модуль tabulate). Таблица должна состоять из двух колонок и выглядеть примерно так:
Reachable
10.0.0.1
10.0.0.2

Unreachable
10.0.0.3
10.0.0.4
------------------ (факультативно) --------------------------
'''

def host_range_ping_tab(net):
    COLLUMN_R = ['REACHABLE']
    COLLUMN_U = ['UNREACHABLE']
    try:
        hosts = list(map(str, ipaddress.ip_network(net).hosts()))
    except ValueError as e:
        print(e)
    else:
        TUPLE_R = host_ping1(hosts)[0]
        TUPLE_U = host_ping1(hosts)[1]
        print(tabulate(TUPLE_R, headers=COLLUMN_R))
        print()
        print(tabulate(TUPLE_U, headers=COLLUMN_U))


#__________________________________________________________________________
#Задание №1
print(host_ping(IPs))
print(host_ping1(IPs))

#__________________________________________________________________________
#Задание №2
host_range_ping('80.0.1.0/28')

#__________________________________________________________________________
#Задание №3
host_range_ping_tab('173.194.222.0/28')