import base64
import json
import os

from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, Qt
import sys
import logging

from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA

sys.path.append(os.path.join(os.getcwd(), '..'))

from client.main_window_conv import Ui_MainClientWindow
from client.add_contact import AddContactDialog
from client.del_contact import DelContactDialog
from common.errors import ServerError
from common.variables import *

client_logger = logging.getLogger('client')


class ClientMainWindow(QMainWindow):
    """Main client window class"""
    def __init__(self, database, transport, keys):
        super().__init__()

        self.database = database
        self.transport = transport

        # -- Message Decoder object with preloaded keys
        self.decrypter = PKCS1_OAEP.new(keys)

        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        self.ui.menu_exit.triggered.connect(qApp.exit)

        self.ui.btn_send.clicked.connect(self.send_message)

        # -- Add contact
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        # -- Remove contact
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.current_chat_key = None
        self.encryptor = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        # -- Send double click event on a client list objects to an event handler
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    def set_disabled_input(self):
        """Disable input fields and buttons"""
        self.ui.label_new_message.setText('Для выбора получателя дважды кликните на нем в окне контактов.')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        # -- Message textarea and send button are disabled before user been selected
        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

    def history_list_update(self):
        """Fill in a messages history"""
        # -- Get messages sorted by date
        messages_list = sorted(self.database.get_history(self.current_chat), key=lambda item: item[3])

        # -- Create model if not exists
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)

        # -- Clear messages textarea
        self.history_model.clear()

        # -- Get only 20 messages from a messages history
        length = len(messages_list)
        start_index = 0
        if length > 20:
            start_index = length - 20

        # -- Fill in messages. Add different color and align for users message
        for i in range(start_index, length):
            item = messages_list[i]
            if item[1] == 'in':
                mess = QStandardItem(f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Исходящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    def select_active_user(self):
        """Method handler of double-clicked contact event"""
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.set_active_user()

    def set_active_user(self):
        """Set active chat user method"""
        try:
            self.current_chat_key = self.transport.key_request(
                self.current_chat)
            client_logger.debug(f'Public key loaded for "{self.current_chat}"')
            if self.current_chat_key:
                self.encryptor = PKCS1_OAEP.new(
                    RSA.import_key(self.current_chat_key))
        except (OSError, json.JSONDecodeError):
            self.current_chat_key = None
            self.encryptor = None
            client_logger.debug(f'Can\'t get public key for user "{self.current_chat}"')

        # -- Show error message if public key for this user is unavailable -----
        if not self.current_chat_key:
            self.messages.warning(
                self, 'Ошибка', 'Для выбранного пользователя нет ключа шифрования.')
            return

        # -- Set label value and active buttons
        self.ui.label_new_message.setText(f'Введите сообщенние для {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)

        # -- Fill in the messages list window for selected contact
        self.history_list_update()

    def clients_list_update(self):
        """Update contacts list method"""
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)

        self.ui.list_contacts.setModel(self.contacts_model)

    def add_contact_window(self):
        """Add contact window method"""
        global select_dialog

        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    def add_contact_action(self, item):
        """Adding contact handler method"""
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, new_contact):
        """Add contact to dbs method"""
        try:
            self.transport.add_contact(new_contact)
        except ServerError as err:
            self.messages.critical(self, 'Server error while contact adding', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            client_logger.info(f'Contact {new_contact} has benn added')
            self.messages.information(self, 'Успех', 'Контакт успешно добавлен.')

    def delete_contact_window(self):
        """Remove contact method"""
        global remove_dialog

        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    def delete_contact(self, item):
        """Contact remove handler method"""
        selected = item.selector.currentText()
        try:
            self.transport.remove_contact(selected)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.del_contact(selected)
            self.clients_list_update()
            client_logger.info(f'Contact {selected} removed')
            self.messages.information(self, 'Успех', 'Контакт успешно удалён.')
            item.close()
            # -- If removed active user need to deactivate input fields
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    def send_message(self):
        """Send user message method"""
        # -- Get message from a textarea and cleans
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return

        # -- Encrypt message with receiver public key -------------------
        message_text_encrypted = self.encryptor.encrypt(
            message_text.encode('utf8'))
        message_text_encrypted_base64 = base64.b64encode(
            message_text_encrypted)

        try:
            self.transport.send_message(self.current_chat, message_text_encrypted_base64.decode('ascii'))
            pass
        except ServerError as err:
            self.messages.critical(self, 'Ошибка', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
            self.close()
        else:
            self.database.save_message(self.current_chat, 'out', message_text)
            client_logger.debug(f'Message been sent for {self.current_chat}: {message_text}')
            self.history_list_update()

    @pyqtSlot(dict)
    def message(self, message):
        """New message receiver slot. Decrypting incoming message.
        Change current chat if message from other client received
        """
        # -- Getting bytes string --------------
        encrypted_message = base64.b64decode(message[MESSAGE_TEXT])

        # -- Try to decrypt a message ----------
        try:
            decrypted_message = self.decrypter.decrypt(encrypted_message)
        except (ValueError, TypeError):
            self.messages.warning(
                self, 'Ошибка', 'Не удалось декодировать сообщение.')
            return

        # -- Save message in db and update messages history or opening a new chat
        self.database.save_message(
            self.current_chat, 'in', decrypted_message.decode('utf8'))

        sender = message[SENDER]
        if sender == self.current_chat:
            self.history_list_update()
        else:
            # -- Check user at contacts list ---------------------
            if self.database.check_contact(sender):
                # -- Ask user to start a chat with this contact --
                user_action = self.messages.question(self, 'Новое сообщение',
                                                     f'Получено новое сообщение от {sender}, открыть чат с ним?',
                                                     QMessageBox.Yes, QMessageBox.No)
                if user_action == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                print('NO')
                # -- Ask to add a new contact to contacts list --
                user_action = self.messages.question(self, 'Новое сообщение',
                                                     f'Получено новое сообщение от {sender}.\n'
                                                     f' Данного пользователя нет в вашем контакт-листе.\n'
                                                     f' Добавить в контакты и открыть чат с ним?',
                                                     QMessageBox.Yes, QMessageBox.No)
                if user_action == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    # -- Need to save message, or it'll be lost. Because in a previous call this client doesn't exist
                    self.database.save_message(
                        self.current_chat, 'in', decrypted_message.decode('utf8'))

                    self.set_active_user()

    @pyqtSlot()
    def connection_lost(self):
        """Connection lost slot"""
        self.messages.warning(self, 'Сбой соединения', 'Потеряно соединение с сервером. ')
        self.close()

    @pyqtSlot()
    def sig_205(self):
        """Updating database by server command slot"""
        if self.current_chat and not self.database.check_user(
                self.current_chat):
            self.messages.warning(
                self,
                'Сочувствую',
                'К сожалению собеседник был удалён с сервера.')
            self.set_disabled_input()
            self.current_chat = None
        self.clients_list_update()

    def make_connection(self, trans_obj):
        """Method to connect a transport signal with main client window slots"""
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)
        trans_obj.message_205.connect(self.sig_205)
