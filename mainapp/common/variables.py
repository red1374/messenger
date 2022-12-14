"""Константы"""
import logging

# Порт по умолчанию для сетевого взаимодействия
DEFAULT_PORT = 7777
# IP адрес по умолчанию для подключения клиента
DEFAULT_IP_ADDRESS = '127.0.0.1'
# Максимальная очередь подключений
MAX_CONNECTIONS = 5
# Максимальная длинна сообщения в байтах
MAX_PACKAGE_LENGTH = 1024
# Кодировка проекта
ENCODING = 'utf-8'
# Текущий уровень логирования
LOGGING_LEVEL = logging.DEBUG

SERVER_CONFIG = 'server.ini'

# Протокол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'
GET_CONTACTS = 'get_contacts'
ADD_CONTACT = 'add_contact'
REMOVE_CONTACT = 'remove_contact'
LIST_INFO = 'list'
DATA = 'bin'
PUBLIC_KEY = 'pubkey'

# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
USERS_REQUEST = 'get_users'
PUBLIC_KEY_REQUEST = 'pubkey_need'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'text'
EXIT = 'exit'


# БД
SERVER_DATABASE = 'db.sqlite'

RESPONSE_200 = {RESPONSE: 200}

RESPONSE_202 = {RESPONSE: 202, LIST_INFO: None}

RESPONSE_400 = {RESPONSE: 400, ERROR: None}

RESPONSE_205 = {RESPONSE: 205}

RESPONSE_511 = {RESPONSE: 511, DATA: None}
