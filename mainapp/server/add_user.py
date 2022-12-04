from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel, QMessageBox
from PyQt5.QtCore import Qt
import hashlib
import binascii


class RegisterUser(QDialog):
    """Register user dialog window class"""

    def __init__(self, database, server):
        super().__init__()

        self.db = database
        self.server = server

        # -- Window settings ---------------------------------
        self.setWindowTitle('Регистрация')
        self.setFixedSize(175, 183)
        self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # -- Username field label ----------------------------
        self.label_username = QLabel('Имя пользователя:', self)
        self.label_username.setFixedSize(150, 15)
        self.label_username.move(10, 10)

        # -- Username input field ----------------------------
        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        # -- Password field label ----------------------------
        self.label_passwd = QLabel('Пароль:', self)
        self.label_passwd.setFixedSize(150, 15)
        self.label_passwd.move(10, 55)

        # -- Password input field ----------------------------
        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(154, 20)
        self.client_passwd.move(10, 75)
        self.client_passwd.setEchoMode(QLineEdit.Password)

        # -- Password confirmation field label ---------------
        self.label_conf = QLabel('Введите подтверждение:', self)
        self.label_conf.setFixedSize(150, 15)
        self.label_conf.move(10, 100)

        # -- Password confirmation field ---------------------
        self.client_conf = QLineEdit(self)
        self.client_conf.setFixedSize(154, 20)
        self.client_conf.move(10, 120)
        self.client_conf.setEchoMode(QLineEdit.Password)

        self.btn_ok = QPushButton('Сохранить', self)
        self.btn_ok.move(10, 150)
        self.btn_ok.clicked.connect(self.save_data)

        self.btn_cancel = QPushButton('Выход', self)
        self.btn_cancel.move(90, 150)
        self.btn_cancel.clicked.connect(self.close)

        self.messages = QMessageBox()

        self.show()

    def save_data(self):
        """Saving new user data to database"""
        if not self.client_name.text():
            self.messages.critical(
                self, 'Ошибка', 'Не указано имя пользователя.')
            return
        elif self.client_passwd.text() != self.client_conf.text():
            self.messages.critical(
                self, 'Ошибка', 'Введённые пароли не совпадают.')
            return
        elif self.db.check_user(self.client_name.text()):
            self.messages.critical(
                self, 'Ошибка', 'Пользователь уже существует.')
            return
        else:
            # -- Generating password hash. Using username in a lowercase as a Solt
            passwd_bytes = self.client_passwd.text().encode('utf-8')
            salt = self.client_name.text().lower().encode('utf-8')
            passwd_hash = hashlib.pbkdf2_hmac(
                'sha512', passwd_bytes, salt, 10000)
            self.db.add_user(
                self.client_name.text(),
                binascii.hexlify(passwd_hash))
            self.messages.information(
                self, 'Успех', 'Пользователь успешно зарегистрирован.')

            # -- Send a signal to a clients to update users list -----
            self.server.service_update_lists()
            self.close()


if __name__ == '__main__':
    app = QApplication([])
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    dial = RegisterUser(None, None)
    app.exec_()
