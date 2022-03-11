import os
import sys,json
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE

# from common.utils import get_message, send_message

def get_message(client_response):
    if isinstance(client_response, bytes):
        json_response = client_response.decode('utf-8')
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise TypeError


def send_message(message):
    if not isinstance(message, dict):
        raise TypeError
    js_message = json.dumps(message)
    return js_message.encode('utf-8')




class TestGettingConfigs(unittest.TestCase):
    msg_correct = {"IP":"127.0.0.1","port":"8888"}
    msg_wrong = ['IP', "127.0.0.1", "port", "8888"]
    message = {ACTION: 200}
    tMsg = 'Привет'

    def SetUp(self):
        pass

    def tearDown(self):
        pass

    def testGetMsgCorrectValue(self):
        '''Тестирование корректности обработки функцией get_message
                сообщений от сервера или клиента'''
        self.assertEqual(get_message(send_message(self.msg_correct)), self.msg_correct)

    def testGetMsgRaiseByte(self):
        '''Тестирование возникновения исключения при поступлении ответа (client_response)
        в неправильном формате (не в byte) '''
        self.assertRaises(TypeError, get_message,self.msg_wrong)

    def testSendMessage(self):
        '''Тестирование функции send_message (правильности преобразования сообщения)'''
        self.assertEqual(send_message(self.msg_correct), json.dumps(self.msg_correct).encode('utf-8'))

    def testRaiseSendMessage(self):
        '''тестирование возникновения исключения TypeError
        возникающего в функции send_message при попытке отправить сообщение в неправильном формате'''
        self.assertRaises(TypeError, send_message, self.tMsg)



if __name__ == '__main__':
    unittest.main()
