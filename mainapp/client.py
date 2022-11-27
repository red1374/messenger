import sys
import os

from PyQt5.QtWidgets import QApplication

from common.variables import *
from common.utils import get_params

from common.errors import ServerError

from client.database import ClientDatabase
from client.transport import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog

client_log = logging.getLogger('client')


def get_server_params(params_list):
    """ Get server connection parameters """
    try:
        server_address = params_list['ip']
        server_port = int(params_list['p'])
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except KeyError:
        server_address = DEFAULT_IP_ADDRESS
        server_port = DEFAULT_PORT
        client_log.info(f'Setting up a default port and address values')
    except ValueError:
        client_log.critical(f'Wrong port number: {server_port}. Value must be between 1024 and 65535')
        sys.exit(1)

    return (
        server_address,
        server_port
    )


def get_client_name(params_list):
    """ Get clients name from command line params or request it with UserDialog window """
    try:
        username = params_list['n'].strip()
    except KeyError:
        # -- Show user dialog to enter client_name or exit
        start_dialog = UserNameDialog()
        client_app.exec_()

        if start_dialog.ok_pressed:
            username = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    return username


if __name__ == '__main__':
    params = get_params()

    server_address, server_port = get_server_params(params)

    # -- Application introduction ---------------------------
    print(f'-- Client application --')

    # -- Create client GUI ----------------------------------
    client_app = QApplication(sys.argv)

    client_name = get_client_name(params)
    print(f'You logged in as "{client_name}"')

    # -- Create client DB object ---------------------------
    database = ClientDatabase(client_name)

    # -- Initiate client transport object ------------------
    try:
        transport = ClientTransport(server_port, server_address, database, client_name)
    except ServerError as error:
        client_log.error(f'Server returned an error: {error.text}')
        sys.exit(1)
    transport.setDaemon(True)
    transport.start()

    # -- Create client window GUI --------------------------
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Messanger v2.0 - {client_name}')
    client_app.exec_()

    # -- Stop transport if clint window is closed
    transport.transport_shutdown()
    transport.join()
