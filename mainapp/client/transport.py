import os
import socket
import sys
import time
import logging
import json
import threading
import hashlib
import hmac
import binascii
from pydoc import cli

from PyQt5.QtCore import pyqtSignal, QObject

sys.path.insert(0, os.path.join(os.getcwd(), '..'))

from common.utils import send_message, get_message
from common.variables import *
from common.errors import ServerError, ReqFieldMissingError
from common.decorators import Log
client_log = logging.getLogger('client')
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    """ Transport class - to communicate with the server """

    # -- Lost connection and new message signal
    new_message = pyqtSignal(dict)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username, passwd, keys):
        # -- Parents constructors call
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.account_name = username
        self.password = passwd
        self.transport = None
        self.keys = keys
        self.server_address = ip_address
        self.server_port = port

        self.connection_init()

        # -- Update tables known users and contacts -------------
        try:
            self.user_list_update()
            self.contacts_list_request()
        except OSError as err:
            if err.errno:
                client_log.critical(f'Server connection lost on update users list stage.')
                raise ServerError('Server connection lost!')
            client_log.error('Timeout at users list update stage')
        except json.JSONDecodeError:
            client_log.critical(f'Server connection lost on update users list stage.')
            raise ServerError('Server connection lost!')

        # -- Setting flag that transport is still running ------
        self.running = True

    def connection_init(self):
        """ Server connection initiation method """
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_log.info(f'Starting client transport socket')

        # -- Timeout is required to release a socket --------
        self.transport.settimeout(5)

        # -- Try to create connection for 5 tries max -------
        connected = False
        for i in range(5):
            client_log.info(f'Try to connect to a server №{i + 1}')
            try:
                client_log.debug((self.server_address, self.server_port))
                self.transport.connect((self.server_address, self.server_port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        # -- Raise an exception if connection is failed ----
        if not connected:
            client_log.critical('Can\'t establish a connection with a server!')
            raise ServerError('Can\'t establish a connection with a server!')

        client_log.debug('Connection is set!')

        # -- Starting authentication process ---------------
        # -- Getting passwor hash --------------------------
        passwd_bytes = self.password.encode('utf-8')
        salt = self.account_name.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)

        client_log.debug(f'Passwd hash ready: {passwd_hash_string}')

        # -- Getting public key and decoding it from bytes -
        pubkey = self.keys.publickey().export_key().decode('ascii')

        # -- Authorizing on the server ------------------------
        with socket_lock:
            # -- Try to send a presence message to a server ----
            try:
                client_log.info(f'Starting to send presence message')
                send_message(self.transport, self.create_presence(pubkey))
                client_log.info(f'Presence message sent!')
                answer = get_message(self.transport)
                client_log.info(f'Getting answer from a server: {answer}')

                # -- If server response an error throw an exceptions ------
                if RESPONSE in answer:
                    if answer[RESPONSE] == 400:
                        raise ServerError(answer[ERROR])
                    elif answer[RESPONSE] == 511:
                        # -- If it's ok continue authorization process ----
                        ans_data = answer[DATA]
                        hash = hmac.new(passwd_hash_string, ans_data.encode('utf-8'), 'MD5')
                        digest = hash.digest()

                        my_ans = RESPONSE_511
                        my_ans[DATA] = binascii.b2a_base64(
                            digest).decode('ascii')
                        send_message(self.transport, my_ans)
                        self.process_server_answer(self, get_message(self.transport))
            except (OSError, json.JSONDecodeError) as err:
                client_log.debug(f'Connection error.', exc_info=err)
                raise ServerError('Connection error while client authorization')

    def create_presence(self, pubkey):
        """ Method to generate a presence dict """
        client_log.debug(f'Presence message create')
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.account_name,
                PUBLIC_KEY: pubkey
            }
        }

        client_log.debug(f'Presence message from a user {self.account_name}: {out}')

        return out

    def create_exit_message(self):
        """ Method to generate "Exit" message """
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    @Log
    def process_server_answer(self, message):
        """ Processing server answer """
        client_log.debug(f'Server response message: {message}')
        if RESPONSE in message:
            if int(message[RESPONSE]) == 200:
                return '200 : OK'
            elif int(message[RESPONSE]) == 400:
                raise ServerError(f'400 : {message[ERROR]}')
            elif message[RESPONSE] == 205:
                self.user_list_update()
                self.contacts_list_request()
                self.message_205.emit()
            else:
                client_log.debug(f'Unknown server response code: {message[RESPONSE]}')
        # -- If this message from another user, add it to db
        elif ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
            client_log.debug(f'Got a message from a user {message[SENDER]}:{message[MESSAGE_TEXT]}')

            # -- Send a signal about a new message -------------
            self.new_message.emit(message)

    def contacts_list_request(self):
        """ Users list request from server """
        self.database.contacts_clear()
        client_log.info(f'Contacts list request for user {self.account_name}')
        request = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.account_name
        }
        client_log.debug(f'Request created: {request}')
        with socket_lock:
            send_message(self.transport, request)
            answer = get_message(self.transport)
        client_log.debug(f'Answer received: {answer}')

        # -- Add contacts to a contacts table ---------------
        if RESPONSE in answer and answer[RESPONSE] == 202:
            for contact in answer[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            client_log.error('Contacts list request failed!')

    def user_list_update(self):
        """ Update table with known users """
        client_log.debug(f'Known users list request for {self.account_name}')
        request = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }
        client_log.debug(f'Known users list request dict: {request}')
        with socket_lock:
            client_log.debug(f'Users list params: {self.transport}, {request}')
            send_message(self.transport, request)
            answer = get_message(self.transport)

        if RESPONSE in answer and answer[RESPONSE] == 202:
            self.database.add_users(answer[LIST_INFO])
        else:
            client_log.error('Known users list update has failed.')

    def key_request(self, user):
        """ Users public key requests form a server method """
        client_log.debug(f'Public key request for "{user}"')
        request = {
            ACTION: PUBLIC_KEY_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: user
        }
        with socket_lock:
            send_message(self.transport, request)
            answer = get_message(self.transport)

        if RESPONSE in answer and answer[RESPONSE] == 511:
            return answer[DATA]
        else:
            client_log.error(f'Can\'t get public key for user "{user}"')

    def add_contact(self, contact):
        """ Add user contact """
        client_log.info(f'Contact adding: {contact}')
        request = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.account_name,
            ACCOUNT_NAME: contact
        }

        with socket_lock:
            send_message(self.transport, request)
            self.process_server_answer(self, get_message(self.transport))

    def remove_contact(self, contact):
        """ Remove user contact from a server """
        client_log.info(f'Removing user contact: {contact}')
        request = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.account_name,
            ACCOUNT_NAME: contact
        }

        with socket_lock:
            send_message(self.transport, request)
            self.process_server_answer(self, get_message(self.transport))

    def transport_shutdown(self):
        """ Method to close a connection and send an exit message """
        self.running = False

        with socket_lock:
            try:
                send_message(self.transport, self.create_exit_message())
            except OSError:
                pass
        client_log.debug('End of transport job')
        self.transport.close()
        time.sleep(0.5)

    def send_message(self, to, message):
        """ Method to send a message to a server """
        client_log.info(f'Sending a message: {message}')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        client_log.info(f'Sending a dict: {message_dict}')

        # -- Wait for socket release before message been sent ----
        with socket_lock:
            send_message(self.transport, message_dict)
            self.process_server_answer(self, get_message(self.transport))
            client_log.info(f'Message for user "{to}" has been sent')

    def run(self):
        client_log.debug('Starting messages receiver process')
        while self.running:
            # -- Wait for 1 second and try to capture a socket ---
            time.sleep(1)
            message = None
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        client_log.critical(f'Server connection lost')
                        self.running = False
                        self.connection_lost.emit()
                # -- Process connection problems -----------------
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    client_log.debug(f'Server connection lost')
                    self.running = False
                    self.connection_lost.emit()
                finally:
                    if type(self.transport) == "<class 'socket.socket'>":
                        self.transport.settimeout(5)

            # -- Call handler function if message is received ----
            if message:
                client_log.debug(f'Server message received : {message}')
                self.process_server_answer(self, message)
