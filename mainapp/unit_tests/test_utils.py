import json
import sys
import os
import unittest

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

sys.path.insert(0, os.path.join(os.getcwd(), '..'))

from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE, ENCODING, DEFAULT_IP_ADDRESS,\
    DEFAULT_PORT, MAX_CONNECTIONS
from common.utils import get_message, send_message


class TestUtils(unittest.TestCase):
    def setUp(self) -> None:
        self.message = {
            ACTION: PRESENCE,
            TIME: 1.1,
            USER: {
                ACCOUNT_NAME: 'Guest',
            },
        }

        """ Create server socket """
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((DEFAULT_IP_ADDRESS, DEFAULT_PORT))
        self.server_socket.listen(MAX_CONNECTIONS)

        """ Create client socket """
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((DEFAULT_IP_ADDRESS, DEFAULT_PORT))

        self.server_client_socket = None

    def tearDown(self) -> None:
        """ Close sockets """
        self.client_socket.close()
        self.server_socket.close()
        self.server_client_socket.close()

    def test_send_message_true(self):
        """ Tests correct message conversion with send_message function """
        self.server_client_socket, address = self.server_socket.accept()

        send_message(self.client_socket, self.message)
        answer = self.server_client_socket.recv(1024)

        exspacted_answare = json.dumps(self.message).encode(ENCODING)

        self.assertEqual(answer, exspacted_answare)

    def test_send_message_false(self):
        """ Tests correct message conversion with send_message function """
        self.server_client_socket, address = self.server_socket.accept()

        self.assertRaises(TypeError, send_message, [self.client_socket, ''])

    def test_get_message_true(self):
        """ Tests correct message processing with get_message function """
        self.server_client_socket, address = self.server_socket.accept()

        send_message(self.client_socket, self.message)
        response_message = get_message(self.server_client_socket)

        self.assertEqual(self.message, response_message)

    def test_get_message_type_error(self):
        """ Tests wrong message type processing with get_message function """
        self.server_client_socket, address = self.server_socket.accept()

        wrong_message = 'String'
        self.client_socket.send(wrong_message.encode(ENCODING))

        self.assertRaises(ValueError, get_message, self.server_client_socket)


if __name__ == '__main__':
    unittest.main()
