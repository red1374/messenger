import os
import sys
import logging

sys.path.append(os.path.join(os.getcwd(), '..'))

from client.database import ClientDatabase
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt

client_logger = logging.getLogger('client')


class AddContactDialog(QDialog):
    """ Dialog window to select a user for adding to contact list """
    def __init__(self, transport, database):
        super().__init__()
        self.transport = transport
        self.database = database

        self.setFixedSize(350, 120)
        self.setWindowTitle('Выберите контакт для добавления:')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Выберите контакт для добавления:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_refresh = QPushButton('Обновить список', self)
        self.btn_refresh.setFixedSize(100, 30)
        self.btn_refresh.move(60, 60)

        self.btn_ok = QPushButton('Добавить', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        # -- Get possible contacts list to add ----
        self.possible_contacts_update()
        # -- Set event handler to Update button ---
        self.btn_refresh.clicked.connect(self.update_possible_contacts)

    def possible_contacts_update(self):
        """ Get possible contacts to add a new one """
        self.selector.clear()
        # -- Get current user contacts ----------------
        contacts_list = set(self.database.get_contacts())
        # -- Get all users list -----------------------
        users_list = set(self.database.get_users())

        # -- Remove yourself from a users list ---------
        users_list.remove(self.transport.account_name)

        # -- Create possible contacts list -------------
        self.selector.addItems(users_list - contacts_list)

    def update_possible_contacts(self):
        """ Update known users table and possible contacts list """
        try:
            self.transport.user_list_update()
        except OSError:
            pass
        else:
            client_logger.debug('Users list update is complete')
            self.possible_contacts_update()

