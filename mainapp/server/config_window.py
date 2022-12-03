from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
import os


class ConfigWindow(QDialog):
    """ Configuration window class """

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.initUI()

    def initUI(self):
        # -- Window settings ----------------------------------
        self.setWindowTitle('Настройки сервера')
        self.setFixedSize(390, 250)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        # -- DB file label ------------------------------------
        self.db_path_label = QLabel('Путь до файла БД: ', self)
        self.db_path_label.setFixedSize(240, 15)
        self.db_path_label.move(10, 10)

        # -- DB file path label -------------------------------
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(260, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        # -- Select DB path button ----------------------------
        self.db_path_button = QPushButton('Обзор...', self)
        self.db_path_button.move(278, 25)

        # -- Db file name label -------------------------------
        self.db_file_label = QLabel('Имя файла БД: ', self)
        self.db_file_label.setFixedSize(180, 15)
        self.db_file_label.move(10, 68)

        # -- Field for DB file name ---------------------------
        self.db_file = QLineEdit(self)
        self.db_file.setFixedSize(150, 20)
        self.db_file.move(220, 66)

        # -- Port number label --------------------------------
        self.port_label = QLabel('Номер порта для соединения: ', self)
        self.port_label.setFixedSize(180, 15)
        self.port_label.move(10, 108)

        # -- Port number input field -------------------------
        self.port = QLineEdit(self)
        self.port.setFixedSize(150, 20)
        self.port.move(220, 108)

        # -- Connection address label ------------------------
        self.ip_label = QLabel('IP адрес для приема соединений: ', self)
        self.ip_label.setFixedSize(200, 15)
        self.ip_label.move(10, 148)

        # -- Note for empty field ----------------------------
        self.ip_note = QLabel('Оставьте это поле пустым, для\nприема соединений с любых\nадресов', self)
        self.ip_note.setFixedSize(200, 45)
        self.ip_note.move(10, 168)

        # -- Connection address input field ------------------
        self.ip = QLineEdit(self)
        self.ip.setFixedSize(150, 20)
        self.ip.move(220, 148)

        # -- Save settings button ----------------------------
        self.save_btn = QPushButton('Сохранить', self)
        self.save_btn.move(185, 205)

        # -- Close dialog button -----------------------------
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(278, 205)
        self.close_button.clicked.connect(self.close)

        self.db_path_button.clicked.connect(self.open_file_dialog)
        self.show()

        # -- Fill in the fields value with config data -------
        self.db_path.insert(self.config['SETTINGS']['Database_path'])
        self.db_file.insert(self.config['SETTINGS']['Database_file'])
        self.port.insert(self.config['SETTINGS']['Default_port'])
        self.ip.insert(self.config['SETTINGS']['Listen_Address'])

        self.save_btn.clicked.connect(self.save_server_config)

    def open_file_dialog(self):
        """ Select file directory dialog window method """

        global dialog

        dialog = QFileDialog(self)
        path = dialog.getExistingDirectory()
        path = path.replace('/', '\\')
        self.db_path.clear()
        self.db_path.insert(path)

    def save_server_config(self):
        """ Save server configuration """

        global config_window

        message = QMessageBox()
        self.config['SETTINGS']['Database_path'] = self.db_path.text()
        self.config['SETTINGS']['Database_file'] = self.db_file.text()
        try:
            port = int(self.port.text())
        except ValueError:
            message.warning(self, 'Ошибка', 'Порт должен быть числом')
        else:
            self.config['SETTINGS']['Listen_Address'] = self.ip.text()
            if 1023 < port < 65536:
                self.config['SETTINGS']['Default_port'] = str(port)
                dir_path = os.path.dirname(os.path.realpath(__file__))
                dir_path = os.path.join(dir_path, '..')
                with open(f"{dir_path}/{'server.ini'}", 'w') as conf:
                    self.config.write(conf)
                    message.information(
                        self, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    self, 'Ошибка', 'Порт должен быть от 1024 до 65536')
