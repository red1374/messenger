import configparser
import logging
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

sys.path.append(os.path.join(os.getcwd(), '..'))

from server.db import Storage
from server.core import MessageProcessor
from server.main_window import MainWindow

from common.variables import DEFAULT_IP_ADDRESS, DEFAULT_PORT
from common.utils import get_params

from common.decorators import Log

server_log = logging.getLogger('server')


@Log
def config_load():
    """Load server settings file"""
    config = configparser.ConfigParser()
    dir_path = os.getcwd()
    config.read(f"{dir_path}/{'server.ini'}")

    if 'SETTINGS' not in config:
        config['SETTINGS'] = {}
        config['SETTINGS'] = {
            'Database_path': '',
            'Database_file': '',
            'Default_port': '',
            'Listen_Address': '',
        }

    return config


@Log
def main():
    # - Load server config ---------------------------------------
    config = config_load()

    # -- Load parameters from command line or setting up a default
    # -- values if config is empty
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

    # -- Create database object ----------------------------------
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

    # -- Start server background process ------------------------
    server = MessageProcessor(db, listen_address, listen_port)
    server.daemon = True
    server.start()

    # -- Creating server user interface ---------------------
    server_app = QApplication(sys.argv)
    server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    main_window = MainWindow(db, server, config)

    # -- Starting server GUI --------------------------------
    server_app.exec_()

    # -- Stop event handler when all windows are closed -----
    server.running = False


if __name__ == '__main__':
    main()
