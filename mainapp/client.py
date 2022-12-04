import os
import sys

from Cryptodome.PublicKey import RSA

from PyQt5.QtWidgets import QApplication, QMessageBox

from common.variables import *
from common.utils import get_params

from common.errors import ServerError

from client.database import ClientDatabase
from client.transport import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog

client_log = logging.getLogger('client')


def get_server_params(params_list):
    """Getting server connection parameters"""
    try:
        server_address = params_list['ip']
        server_port = int(params_list['port'])
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except KeyError:
        server_address = DEFAULT_IP_ADDRESS
        server_port = DEFAULT_PORT
        client_log.info(f'Setting up a default port and address values')
    except ValueError:
        client_log.critical(f'Wrong port number: {server_port}. Value must be between 1024 and 65535')
        sys.exit(1)

    try:
        client_name = params_list['name']
    except KeyError:
        client_name = None

    try:
        client_passwd = params_list['p']
    except KeyError:
        client_passwd = ''

    return (
        server_address,
        server_port,
        client_name,
        client_passwd
    )


def get_client_data(start_dialog):
    """Getting clients name and password from UserDialog window"""

    # -- Show user dialog to enter client_name or exit
    client_app.exec_()

    if start_dialog.ok_pressed:
        name = start_dialog.client_name.text()
        passwd = start_dialog.client_passwd.text()
        client_log.debug(f'Using USERNAME = {name}, PASSWD = {passwd}.')
    else:
        exit(0)

    return name, passwd


if __name__ == '__main__':
    params = get_params()

    server_address, server_port, client_name, client_passwd = get_server_params(params)

    # -- Application introduction ---------------------------
    print(f'-- Client application --')

    # -- Create client GUI ----------------------------------
    client_app = QApplication(sys.argv)

    start_dialog = UserNameDialog()

    if not client_name:
        client_name, client_passwd = get_client_data(start_dialog)

    print(f'You logged in as "{client_name}"')

    # -- Upload keys from .key files or generate a new one if they are not exist
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    # !!!keys.publickey().export_key()
    client_log.debug("Keys successfully loaded.")

    # -- Create client DB object ---------------------------
    database = ClientDatabase(client_name)

    # -- Initiate client transport object ------------------
    try:
        transport = ClientTransport(server_port, server_address, database, client_name, client_passwd, keys)
    except ServerError as error:
        client_log.error(f'Server returned an error: {error.text}')
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', error.text)
        sys.exit(1)
    transport.setDaemon(True)
    transport.start()

    del start_dialog

    # -- Create client window GUI --------------------------
    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Messanger v2.0 - {client_name}')
    client_app.exec_()

    # -- Stop transport if clint window is closed
    transport.transport_shutdown()
    transport.join()
