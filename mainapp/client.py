"""Программа-клиент"""
import logging
import sys
import socket
import threading
import time
from common.variables import PRESENCE, TIME, USER, ACCOUNT_NAME, EXIT, DESTINATION, SENDER, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, MESSAGE, ACTION, MESSAGE_TEXT
from common.utils import get_message, send_message, get_params, get_message_dict
from common.decorators import Log

import logs.client_log_config
from errors import ReqFieldMissingError, ServerError, NonDictInputError

client_log = logging.getLogger('client')


class Client:
    def __init__(self):
        self.server_port = DEFAULT_PORT
        self.server_address = DEFAULT_IP_ADDRESS

    @Log
    def create_presence(self, account_name='Guest'):
        """
        Method to generate presence dict
        :param account_name:
        :return:
        """

        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }
        client_log.debug(f'Presence message from a user {account_name}: {out}')

        return out

    @Log
    def create_exit_message(self, account_name):
        """ Method to generate "Exit" message """
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: account_name
        }

    @Log
    def process_presence_answer(self, message):
        """
        Processing server answer
        :param message:
        :return:
        """
        client_log.debug(f'Server response message: {message}')
        if RESPONSE in message:
            if int(message[RESPONSE]) == 200:
                return '200 : OK'
            raise ServerError(f'400 : {message[ERROR]}')
        raise ReqFieldMissingError(RESPONSE)

    def message_from_server(self, sock, my_username):
        """
        Processing other clients messages from server
        :param sock: client socket
        :param my_username: current client name
        :return:
        """

        while True:
            try:
                message = get_message(sock)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        DESTINATION in message and SENDER in message and MESSAGE_TEXT in message\
                        and message[DESTINATION] == my_username:
                    print(f'\nMessage from "{message[DESTINATION]}":\n{message[MESSAGE_TEXT]}')
                    client_log.info(f'Message from "{message[DESTINATION]}":\n{message[MESSAGE_TEXT]}')
                else:
                    client_log.error(f'Incorrect server message format: {message}')
            except ValueError:
                client_log.error(f'Cant\'decode message from server')
                sys.exit(1)
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError):
                client_log.error(f'Server connection error')
                sys.exit(1)

    def client_menu(self, sock, my_username):
        """ Function to print out a user menu """
        self.print_menu()
        while True:
            command = input('Enter a command: ')
            if command == 'm':
                self.create_message(self, sock, my_username)
            elif command == 'help':
                self.print_menu()
            elif command == 'exit':
                send_message(sock, self.create_exit_message(self, my_username))
                print('End of transmission')
                client_log.info('Close the chat by user command')
                # The delay is necessary to send a message to the server before closing the program
                time.sleep(0.5)
                break
            else:
                print('Command not found. Enter "help" command to see a menu')

    def print_menu(self):
        """ User a program menu """
        print('Select a command:')
        print('\tm - send a message to other client')
        print('\thelp - get help menu')
        print('\texit - exit the program')

    @Log
    def create_message(self, sock, my_username='Guest'):
        """
        Method asks receiver username and message. After that sends the message
        :param sock:
        :param my_username:
        :return:
        """
        while True:
            to_user = input('Enter a receiver username or "q" to exit: ')
            if to_user == 'q':
                return True
            elif to_user.strip() == my_username:
                print(f'You can\'t send message to yourself!')
            elif to_user.strip():
                to_user = to_user.strip()
                break

        while True:
            message = input(f'Print a message or "q" to exit": ')
            if message == 'q':
                return True
            elif message.strip():
                message = message.strip()
                break

        client_log.info(f'Sending a message: {message}')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: my_username,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        client_log.info(f'Sending a dict: {message_dict}')
        try:
            send_message(sock, message_dict)
        except Exception as e:
            client_log.error(f'Server connection error: {e}')
            sys.exit(1)
        print('-- Message sent --\n')

    def run(self):
        # Get command line params and set default socket params
        params = get_params()

        if not params:
            client_log.critical(f'Empty required params: server_address and server_post!')
            sys.exit(1)
        else:
            try:
                self.server_address = params['ip']
                self.server_port = int(params['p'])
                if self.server_port < 1024 or self.server_port > 65535:
                    raise ValueError
            except IndexError:
                self.server_address = DEFAULT_IP_ADDRESS
                self.server_port = DEFAULT_PORT
                client_log.info(f'Setting up a default port and address values')
            except ValueError:
                client_log.critical(f'Wrong port number: {self.server_port}. Value must be between 1024 and 65535')
                sys.exit(1)

        # -- Application introduction --------------------------
        print(f'-- Client application --')
        if not params['n'] or not params['n'].strip():
            while True:
                client_name = input(f'Input your Account name or "q" for exit: ')
                if client_name == 'q':
                    client_log.info(f'Application closed by user')
                    sys.exit(1)
                elif client_name.strip():
                    client_name = client_name.strip()
                    break
        else:
            client_name = params['n'].strip()

        print(f' You logged in as "{client_name}"')

        # -- Initiate client socket ------------------------------
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
            client_log.info(f'Starting client app')
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect((self.server_address, self.server_port))

            message_to_server = self.create_presence(self, client_name)

            client_log.info(f'Sending hello message to the server')
            send_message(client_sock, message_to_server)
            try:
                answer = self.process_presence_answer(self, get_message(client_sock))
                client_log.info(f'Getting answer from a server: {answer}')
            except ServerError as error:
                client_log.error(f'Server returned an error: {error.text}')
                sys.exit(1)
            except ReqFieldMissingError as error:
                client_log.error(error)
                sys.exit(1)
            except ConnectionRefusedError:
                client_log.critical(f'Connection refused error to server {self.server_address}:{self.server_port}')
                sys.exit(1)
            else:
                client_log.info(f'Starting client-server communications')

                # -- Start communication processes with the server ----------------------
                # Start a process for receiving a message from a server
                client_log.info(f'Starting client process for receiving messages from a server')
                receiver = threading.Thread(target=Client.message_from_server, args=(self, client_sock, client_name))
                receiver.daemon = True
                receiver.start()

                # Start a process for sending messages to other clients and starts a user interface
                client_log.info(f'Starting client process for sending messages to other clients')
                user_interface = threading.Thread(target=Client.client_menu, args=(self, client_sock, client_name))
                user_interface.daemon = True
                user_interface.start()

                # Closing the connection if one of the processes are stopped
                while True:
                    time.sleep(1)
                    if receiver.is_alive() and user_interface.is_alive():
                        continue
                    break


if __name__ == '__main__':
    client = Client()
    client.run()
