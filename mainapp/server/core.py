import sys
import threading
import logging
import select
import socket
import hmac
import binascii
import os

sys.path.append(os.path.join(os.getcwd(), '..'))

from common.variables import *

from common.metaclass import ServerVerifier
from common.descriptors import CheckPort
from common.utils import send_message, get_message
from common.decorators import login_required, Log

server_log = logging.getLogger('server')


class MessageProcessor(threading.Thread, metaclass=ServerVerifier):
    listen_port = CheckPort()

    """Class to work with clients messages. Client-server interface"""
    def __init__(self, db, address, port):
        self.listen_address = address
        self.listen_port = port

        self.clients_list = []  # Client sockets list
        self.clients_names = dict()  # Client names with sockets {client_name: client_socket}
        self.messages_list = []  # Messages from all clients

        self.listen_sockets = None

        self.db = db

        self.sock = None

        self.running = True

        super().__init__()

    @login_required
    def process_client_message(self, message, client):
        """Client message processor. Try to send message from a sender to receiver user if it's ok.
        Processing service messages: contacts list request, client exit request, adding new contact
        request, deleting contact request, known users request, public key request.
        If it's not - return "Bad request" response dict or close connection with this client
        """

        server_log.debug(f'Client message processing : {message}')

        if ACTION in message and TIME in message and \
                message[ACTION] in \
                [PRESENCE, MESSAGE, EXIT, GET_CONTACTS, ADD_CONTACT, REMOVE_CONTACT, USERS_REQUEST, PUBLIC_KEY_REQUEST]:
            if message[ACTION] in PRESENCE and USER in message and ACCOUNT_NAME in message[USER]:
                # -- If this is a presence message authorize user ---------
                self.authorize_user(message, client)

            elif DESTINATION in message and SENDER in message and MESSAGE_TEXT in message \
                    and self.clients_names[message[SENDER]] == client:
                # -- Try to send message to a destination user ------------
                if message[DESTINATION] in self.clients_names:
                    self.db.process_message(message[SENDER], message[DESTINATION])
                    self.process_message(self, message)
                    try:
                        send_message(client, RESPONSE_200)
                    except OSError:
                        self.remove_client(client)
                else:
                    response = RESPONSE_400
                    response['ERROR'] = 'User not registered!'
                    try:
                        send_message(client, response)
                    except OSError:
                        pass

            elif message[ACTION] in EXIT and ACCOUNT_NAME in message and\
                    self.clients_names[message[ACCOUNT_NAME]] == client:
                # -- Close client socket if client exit the chat ---------
                self.remove_client(client)

            # -- Contacts list request ----------------------------
            elif message[ACTION] == GET_CONTACTS and USER in message and \
                    self.clients_names[message[USER]] == client:
                response = RESPONSE_202
                response[LIST_INFO] = self.db.get_contacts(message[USER])
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

            # -- New contact adding ------------------------------
            elif message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                    and self.clients_names[message[USER]] == client:
                self.db.add_contact(message[USER], message[ACCOUNT_NAME])
                try:
                    send_message(client, RESPONSE_200)
                except OSError:
                    self.remove_client(client)

            # -- Deleting contact -------------------------------
            elif message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                    and self.clients_names[message[USER]] == client:
                self.db.remove_contact(message[USER], message[ACCOUNT_NAME])
                try:
                    send_message(client, RESPONSE_200)
                except OSError:
                    self.remove_client(client)

            # -- Known users request ---------------------------
            elif message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message and \
                    self.clients_names[message[ACCOUNT_NAME]] == client:
                response = RESPONSE_202
                response[LIST_INFO] = [user[0] for user in self.db.users_list()]
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

            # -- Public key request -----------------------------------------
            elif message[ACTION] == PUBLIC_KEY_REQUEST and ACCOUNT_NAME in message:
                response = RESPONSE_511
                response[DATA] = self.db.get_pubkey(message[ACCOUNT_NAME])

                if response[DATA]:
                    try:
                        send_message(client, response)
                    except OSError:
                        self.remove_client(client)
                else:
                    response = RESPONSE_400
                    response[ERROR] = 'Нет публичного ключа для данного пользователя'
                    try:
                        send_message(client, response)
                    except OSError:
                        self.remove_client(client)

            # -- Else sending Bad request message -----------------------
            else:
                response = RESPONSE_400
                response[ERROR] = 'Bad Request'
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

    @Log
    def process_message(self, message):
        """ Function try to send a message by destinations name """
        if message[DESTINATION] in self.clients_names and self.clients_names[message[DESTINATION]] in self.listen_sockets:
            # -- Send message to the client with DESTINATION account name -------------------------------
            try:
                send_message(self.clients_names[message[DESTINATION]], message)
            except OSError:
                self.remove_client(message[DESTINATION])

            server_log.info(f'Message sent to a user "{message[DESTINATION]}" from user "{message[SENDER]}"')
        elif message[DESTINATION] in self.clients_names and \
                self.clients_names[message[DESTINATION]] not in self.listen_sockets:
            # -- There's now socket for DESTINATION account name ----------------------------------------
            server_log.error(
                f'Connection with client "{message[DESTINATION]}" is lost!')
            self.remove_client(self.clients_names[message[DESTINATION]])
        else:
            server_log.error(f'There\'s no user with "{message[DESTINATION]}" account name')

    def authorize_user(self, message, sock):
        """Authorize user method"""

        server_log.debug(f'Start auth process for {message[USER][ACCOUNT_NAME]}')
        if message[USER][ACCOUNT_NAME] in self.clients_names.keys():
            response = RESPONSE_400
            response[ERROR] = 'Имя пользователя уже занято.'
            try:
                server_log.debug(f'Username busy, sending {response}')
                send_message(sock, response)
            except OSError:
                server_log.debug('OS Error')
                pass
            self.clients_list.remove(sock)
            sock.close()

        # -- Check if client already registered at server ---------------
        elif not self.db.check_user(message[USER][ACCOUNT_NAME]):
            response = RESPONSE_400
            response[ERROR] = 'Пользователь не зарегистрирован.'
            try:
                server_log.debug(f'Unknown username, sending {response}')
                send_message(sock, response)
            except OSError:
                pass
            self.clients_list.remove(sock)
            sock.close()
        else:
            server_log.debug('Correct username, starting passwd check.')
            # -- Starting authentication process -------------------------
            message_auth = RESPONSE_511
            random_str = binascii.hexlify(os.urandom(64))
            message_auth[DATA] = random_str.decode('ascii')

            # -- Creating password and random string hash
            # -- Saving public key server version
            new_hash = hmac.new(self.db.get_hash(message[USER][ACCOUNT_NAME]), random_str, 'MD5')
            digest = new_hash.digest()
            server_log.debug(f'Auth message = {message_auth}')
            try:
                # -- Send it to a client ------------------------------
                send_message(sock, message_auth)
                answer = get_message(sock)
            except OSError as err:
                server_log.debug('Error in auth, data:', exc_info=err)
                sock.close()
                return

            client_digest = binascii.a2b_base64(answer[DATA])
            # -- If client answer is correct save it to a users list
            if RESPONSE in answer and answer[RESPONSE] == 511 and \
                    hmac.compare_digest(digest, client_digest):
                self.clients_names[message[USER][ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, RESPONSE_200)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])

                # -- Add a client to an active users list and saving public key if it's new
                self.db.user_login(
                    message[USER][ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[USER][PUBLIC_KEY])
            else:
                response = RESPONSE_400
                response[ERROR] = 'Неверный пароль.'
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients_list.remove(sock)
                sock.close()

    def service_update_lists(self):
        """Sends a message with status code 205 to a clients method"""
        for client in self.clients_names:
            try:
                send_message(self.clients_names[client], RESPONSE_205)
            except OSError:
                self.remove_client(self.clients_names[client])

    def init_socket(self):
        """Init server socket method"""
        server_log.info(f'Server started at {self.listen_address}:{self.listen_port}')

        # -- Prepare socket ----------------------------------------------------
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        transport.bind((self.listen_address, self.listen_port))

        # -- Setting up this option to disable "accept" function locking state
        transport.settimeout(0.5)

        # -- Starting listen to a socket ---------------------------------------
        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def remove_client(self, client):
        """Remove client from the client list and form db"""
        server_log.info(f'Client "{client.getpeername()}" is disconnected')
        for name in self.clients_names:
            if self.clients_names[name] == client:
                self.db.user_logout(name)
                del self.clients_names[name]
                break
        self.clients_list.remove(client)
        client.close()

    def run(self):
        """Main Thread cycle.
        Overriding default Thread method "run" and starting it automatically
        """
        self.init_socket()

        while self.running:
            server_log.info(f'Waiting for new client ...')
            try:
                client_socket, client_address = self.sock.accept()
            except OSError as err:
                # -- The error number returns None because it's just a timeout
                # print(err.errno)
                pass
            else:
                server_log.info(f'New client connected from \'{client_address}\'')
                self.clients_list.append(client_socket)

            recv_data_lst = []

            # -- Checking for a clients that are waiting --------------------------------
            try:
                if self.clients_list:
                    recv_data_lst, self.listen_sockets, _ = select.select(
                        self.clients_list, self.clients_list, [], 0)
            except OSError:
                pass

            # -- If client sends data, need to process it's messages or delete it from a clients list
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        server_log.info(
                            f'Creating server response message for client {client_with_message.getpeername()}')
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except ValueError as value_error:
                        server_log.error(f'Client response message error: {value_error}.')
                        self.remove_client(client_with_message)
                    except Exception as error:
                        server_log.error(f'Client response message error: {error}.')
                        self.remove_client(client_with_message)
