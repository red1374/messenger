"""Программа-сервер"""
import configparser
import logging
import os
import select
import socket
import sys
import threading

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from mainapp.server_gui import MainWindow, get_active_users_model, HistoryWindow, get_stat_model, ConfigWindow

sys.path.append(os.path.join(os.getcwd(), '..'))

from common.db import Storage

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, TIME, \
    PRESENCE, MESSAGE, EXIT, MESSAGE_TEXT, USER, ERROR, DEFAULT_IP_ADDRESS, \
    SENDER, DESTINATION, DEFAULT_PORT, RESPONSE_202, RESPONSE_200, RESPONSE_400, LIST_INFO, \
    GET_CONTACTS, ADD_CONTACT, REMOVE_CONTACT, USERS_REQUEST
from common.utils import get_message, send_message, get_params

from common.decorators import Log
from common.metaclass import ServerVerifier
from common.descriptors import CheckPort

server_log = logging.getLogger('server')

# Flag, said that new client was connected
new_connection = False
conflag_lock = threading.Lock()


class Server(threading.Thread, metaclass=ServerVerifier):
    listen_port = CheckPort()

    def __init__(self, db, address, port):
        self.listen_address = address
        self.listen_port = port

        self.clients_list = []  # Client sockets list
        self.clients_names = dict()  # Client names with sockets {client_name: client_socket}
        self.messages_list = []  # Messages from all clients

        self.db = db

        super().__init__()

    @Log
    def process_client_message(self, message, client):
        """
        Client message processor. Add message to a messages list if it's ok.
        If it's not - add response dict or close connection with this client
        :param message: client message
        :param client: client socket object
        :return:
        """
        global new_connection

        server_log.debug(f'Client message processing : {message}')

        if ACTION in message and TIME in message and \
                message[ACTION] in [PRESENCE, MESSAGE, EXIT, GET_CONTACTS, ADD_CONTACT, REMOVE_CONTACT, USERS_REQUEST]:
            if message[ACTION] in PRESENCE and USER in message and ACCOUNT_NAME in message[USER]:
                #  -- Send OK status to a client ----------------
                if message[USER][ACCOUNT_NAME] not in self.clients_names.keys():
                    #  -- Add new client with unique name to clients names list
                    self.clients_names[message[USER][ACCOUNT_NAME]] = client

                    # -- Add information about new client to db
                    client_ip, client_port = client.getpeername()
                    self.db.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)

                    send_message(client, {RESPONSE: 200})
                    with conflag_lock:
                        new_connection = True
                else:
                    # -- Client with this account name is already exists
                    response = RESPONSE_400
                    response['ERROR'] = f' Client with account name "{message[USER][ACCOUNT_NAME]}" is already exists'
                    send_message(client, response)
                    self.clients_list.remove(client)
                    client.close()
                return True
            elif DESTINATION in message and SENDER in message and MESSAGE_TEXT in message:
                # -- Add message to a messages list ----
                if message[DESTINATION] in self.clients_names:
                    self.messages_list.append(message)
                    server_log.debug(f'Add message to a message list : {message[MESSAGE_TEXT]}')
                    self.db.process_message(message[SENDER], message[DESTINATION])
                    send_message(client, {RESPONSE: 200})
                else:
                    response = RESPONSE_400
                    response['ERROR'] = 'User not registered!'
                    send_message(client, response)
                return True
            elif message[ACTION] in EXIT and ACCOUNT_NAME in message:
                # -- Close client socket if client closed the chat
                self.clients_list.remove(self.clients_names[message[ACCOUNT_NAME]])
                self.clients_names[message[ACCOUNT_NAME]].close()
                del self.clients_names[message[ACCOUNT_NAME]]

                self.db.user_logout(message[ACCOUNT_NAME])
                server_log.info('Client disconnected properly')

                with conflag_lock:
                    new_connection = True

                return True
            # -- Contacts list request ----------------------------
            elif message[ACTION] == GET_CONTACTS and USER in message and \
                    self.clients_names[message[USER]] == client:
                response = RESPONSE_202
                response[LIST_INFO] = self.db.get_contacts(message[USER])
                send_message(client, response)

                return True
            # -- New contact adding ------------------------------
            elif message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                    and self.clients_names[message[USER]] == client:
                self.db.add_contact(message[USER], message[ACCOUNT_NAME])
                send_message(client, RESPONSE_200)

                return True
            # -- Deleting contact -------------------------------
            elif message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                    and self.clients_names[message[USER]] == client:
                self.db.remove_contact(message[USER], message[ACCOUNT_NAME])
                send_message(client, RESPONSE_200)

                return True
            # -- Known users request ---------------------------
            elif message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message and \
                    self.clients_names[message[ACCOUNT_NAME]] == client:
                response = RESPONSE_202
                response[LIST_INFO] = [user[0] for user in self.db.users_list()]
                send_message(client, response)

                return True

        # -- Send Bad request status to a client ----------------
        response = RESPONSE_400
        response['ERROR'] = 'Bad Request'
        send_message(client, response)

        return False

    @Log
    def process_message(self, message, listen_socks):
        """
        Function try to send a message by destinations name
        :param message:
        :param listen_socks:
        :return:
        """
        if message[DESTINATION] in self.clients_names and self.clients_names[message[DESTINATION]] in listen_socks:
            # Send message to the client with DESTINATION account name
            send_message(self.clients_names[message[DESTINATION]], message)

            self.db.process_message(message[SENDER], message[DESTINATION])
            server_log.info(f'Message send to user {message[DESTINATION]} from user {message[SENDER]}')
        elif message[DESTINATION] in self.clients_names and \
                self.clients_names[message[DESTINATION]] not in listen_socks:
            # There's now socket for DESTINATION account name
            raise ConnectionError
        else:
            server_log.error(f'There\'s no user with "{message[DESTINATION]}" account name')

    def run(self):
        """
        Load command line parameters to start server. Set default values if parameters are empty or wrong
        Override default Thread method "run" and starts in a thread automatically
        """
        try:
            if self.listen_port < 1024 or self.listen_port > 65535:
                raise ValueError
        except IndexError:
            server_log.critical(f'Insert port number after -\'p\' parameter')
            sys.exit(1)
        except ValueError:
            server_log.critical(f'Wrong port number: {self.listen_port}. Value must be between 1024 and 65535')
            sys.exit(1)

        # Set ip address to listen
        server_log.info(f'Server started at {self.listen_address}:{self.listen_port}')

        # Prepare server socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.listen_address, self.listen_port))

            # Setting this option to disable "accept" function locking state
            server_sock.settimeout(1)

            server_sock.listen(MAX_CONNECTIONS)
            while True:
                server_log.info(f'Waiting for new client ...')
                try:
                    client_socket, client_address = server_sock.accept()
                except OSError as err:
                    # The error number returns None because it's just a timeout
                    # print(err.errno)
                    pass
                else:
                    server_log.info(f'New client connected from \'{client_address}\'')
                    self.clients_list.append(client_socket)

                recv_data_lst = []
                send_data_lst = []

                # Checking for clients activity
                try:
                    if self.clients_list:
                        recv_data_lst, send_data_lst, _ = select.select(self.clients_list, self.clients_list, [], 0)
                except OSError:
                    pass

                # If client sends data, need to process it's messages or delete from a clients list
                if recv_data_lst:
                    for client_with_message in recv_data_lst:
                        try:
                            server_log.info(
                                f'Creating server response message for client {client_with_message.getpeername()}')
                            self.process_client_message(self, get_message(client_with_message), client_with_message)
                        except ValueError as value_error:
                            server_log.error(f'Client response message error.')
                            server_log.info(f'Client "{client_with_message.getpeername()}" is disconnected')
                            self.clients_list.remove(client_with_message)
                        except Exception as error:
                            server_log.error(f'Client response message error: {error}.')
                            server_log.info(f'Client "{client_with_message.getpeername()}" is disconnected')
                            self.clients_list.remove(client_with_message)

                # Send messages to a clients if not empty
                if self.messages_list:
                    for i in self.messages_list:
                        try:
                            self.process_message(self, i, send_data_lst)
                        except Exception:
                            server_log.info(f'Client "{i[DESTINATION]}" is disconnected')
                            self.clients_list.remove(self.clients_names[i[DESTINATION]])
                            del self.clients_names[i[DESTINATION]]
                    self.messages_list.clear()


def main():
    # Load server settings file
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f'{dir_path}/server.ini')

    if 'SETTINGS' not in config:
        config['SETTINGS'] = {}
        config['SETTINGS'] = {
            'Database_path': '',
            'Database_file': '',
            'Default_port': '',
            'Listen_Address': '',
        }

    # Load parameters from command line or setting up a default values if config is empty
    params = get_params()
    try:
        listen_port = params['p']
    except KeyError:
        try:
            listen_port = config['SETTINGS']['Default_port']
        except KeyError:
            listen_port = DEFAULT_PORT

    try:
        listen_address = params['ip']
    except KeyError:
        try:
            listen_address = config['SETTINGS']['Listen_Address']
        except KeyError:
            listen_address = DEFAULT_IP_ADDRESS

    # Create database object
    try:
        db_path = config['SETTINGS']['Database_path']
    except KeyError:
        db_path = ''
    try:
        db_file = config['SETTINGS']['Database_file']
    except KeyError:
        db_file = ''

    db = Storage(os.path.join(
        db_path,
        db_file
    ))

    # Start server background process
    server_obj = Server(db, listen_address, listen_port)
    server_obj.daemon = True
    server_obj.start()

    # Create user interface
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Init main window params. Fill in the active users table
    main_window.statusBar().showMessage('Сервер запущен')
    main_window.active_clients_table.setModel(get_active_users_model(db))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def update_active_users_list():
        """ Update active users list table if new client connected """
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(get_active_users_model(db))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        """ Show users statistics """
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(get_stat_model(db))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        """ Create server configuration window """
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        """ Save server configuration """
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()

        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!'
                    )
            else:
                message.warning(config_window, 'Ошибка', 'Порт должен быть между 1024 и 65536')

    # Create active users list update timer
    timer = QTimer()
    timer.timeout.connect(update_active_users_list)
    timer.start(1000)

    # Bind main window menu items with functions
    main_window.refresh_button.triggered.connect(update_active_users_list)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_button.triggered.connect(server_config)

    # Start server GUI
    server_app.exec_()


if __name__ == '__main__':
    main()
