"""Утилиты"""

import json
import os
import sys
import time
from collections import defaultdict

sys.path.append(os.path.join(os.getcwd(), '..'))

from common.variables import MAX_PACKAGE_LENGTH, ENCODING, MESSAGE, TIME, ACTION, ACCOUNT_NAME, MESSAGE_TEXT, USER
from common.decorators import Log

from errors import NonDictInputError


@Log
def get_message(client):
    """
    Утилита приёма и декодирования сообщения.
    Принимает байты, выдаёт словарь, если принято что-то
    другое возвращает ValueError (ошибку значения)
    """
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        if isinstance(json_response, str):
            response = json.loads(json_response)
            if isinstance(response, dict):
                return response
            raise ValueError
        raise ValueError
    raise ValueError


@Log
def send_message(sock, message):
    """
    Function to encode and send message to a recipient.
    Converts a dict to a string, then make from it bytes and send it to recipient
    """
    if not isinstance(message, dict):
        raise NonDictInputError

    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)


@Log
def get_params():
    """ Get params dict from args list """
    if len(sys.argv) == 0:
        return None

    params = defaultdict()
    params_len = len(sys.argv)
    for index, param in enumerate(sys.argv):
        if param[0] == '-' and params_len > index + 1:
            params[param[1:]] = '' if sys.argv[index + 1][0] == '-' else sys.argv[index + 1]

    return params


@Log
def get_message_dict(message='', account_name='Guest'):
    """ Generate message dict """
    return {
        ACTION: MESSAGE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        },
        MESSAGE_TEXT: message
    }
