import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QLabel, QTableView, QDialog, QPushButton, QLineEdit, \
    QFileDialog, QApplication

from common.db import Storage


def get_active_users_model(db):
    """ Create active users list table """
    users_list = db.active_users_list()
    table_list = QStandardItemModel()
    table_list.setHorizontalHeaderLabels(['Клиент', 'IP Адрес', 'Порт', 'Время подключения'])
    for row in users_list:
        user, ip, port, time = row
        user = QStandardItem(user)
        user.setEditable(False)

        ip = QStandardItem(ip)
        ip.setEditable(False)

        port = QStandardItem(str(port))
        port.setEditable(False)

        time = QStandardItem(str(time.replace(microsecond=0)))
        time.setEditable(False)

        table_list.appendRow([user, ip, port, time])
    return table_list


def get_stat_model(db):
    hist_list = db.message_history()

    table = QStandardItemModel()

    table.setHorizontalHeaderLabels(['Клиент', 'Последний вход', 'Сообщений\nотправлено', 'Сообщений\nполучено'])
    for row in hist_list:
        user, last_seen, sent, recvd = row
        user = QStandardItem(user)
        user.setEditable(False)

        last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
        last_seen.setEditable(False)

        sent = QStandardItem(str(sent))
        sent.setEditable(False)

        recvd = QStandardItem(str(recvd))
        recvd.setEditable(False)

        table.appendRow([user, last_seen, sent, recvd])
    return table


class MainWindow(QMainWindow):
    """ Main window class """
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Exit menu item
        self.exitAction = QAction('Выход', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(qApp.quit)

        # Refresh a list
        self.refresh_button = QAction('Обновить список', self)

        # Show users login history
        self.show_history_button = QAction('История клиентов', self)

        # Show users login history
        self.config_button = QAction('Настройки', self)

        self.statusBar()

        # Toolbar
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_button)

        # Main window settings
        self.setWindowTitle('Сервер сообщений v1.0')
        self.setFixedSize(800, 600)

        self.label = QLabel('Список подключенных клиентов:', self)
        self.label.setFixedSize(400, 15)
        self.label.move(10, 35)

        # Connected users table
        self.active_clients_table = QTableView(self)
        self.active_clients_table.setFixedSize(780, 400)
        self.active_clients_table.move(10, 55)

        self.show()


class HistoryWindow(QDialog):
    """ Users login history window class """
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Main window settings
        self.setWindowTitle('Статистика авторизаций клиентов')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Close window button
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        # Users connection history table
        self.history_table = QTableView(self)
        self.history_table.setFixedSize(580, 620)
        self.history_table.move(10, 10)

        self.show()


class ConfigWindow(QDialog):
    """ Server config window class """
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Window settings
        self.setWindowTitle('Настройки сервера')
        self.setFixedSize(390, 250)

        # DB file label
        self.db_path_label = QLabel('Путь до файла БД: ', self)
        self.db_path_label.setFixedSize(240, 15)
        self.db_path_label.move(10, 10)

        # DB file path label
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(260, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        # Select DB path button
        self.db_path_button = QPushButton('Обзор...', self)
        self.db_path_button.move(278, 25)

        def open_file_dialog():
            global dialog

            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.insert(path)

        self.db_path_button.clicked.connect(open_file_dialog)

        # Db file name label
        self.db_file_label = QLabel('Имя файла БД: ', self)
        self.db_file_label.setFixedSize(180, 15)
        self.db_file_label.move(10, 68)

        # Field for DB file name
        self.db_file = QLineEdit(self)
        self.db_file.setFixedSize(150, 20)
        self.db_file.move(220, 66)

        # Port number label
        self.port_label = QLabel('Номер порта для соединения: ', self)
        self.port_label.setFixedSize(180, 15)
        self.port_label.move(10, 108)

        # Port number input field
        self.port = QLineEdit(self)
        self.port.setFixedSize(150, 20)
        self.port.move(220, 108)

        # Connection address label
        self.ip_label = QLabel('IP адрес для приема соединений: ', self)
        self.ip_label.setFixedSize(200, 15)
        self.ip_label.move(10, 148)

        # Note for empty field
        self.ip_note = QLabel('Оставьте это поле пустым, для\nприема соединений с любых\nадресов', self)
        self.ip_note.setFixedSize(200, 45)
        self.ip_note.move(10, 168)

        # Connection address input field
        self.ip = QLineEdit(self)
        self.ip.setFixedSize(150, 20)
        self.ip.move(220, 148)

        # Save settings button
        self.save_btn = QPushButton('Сохранить', self)
        self.save_btn.move(185, 205)

        # Close dialog button
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(278, 205)
        self.close_button.clicked.connect(self.close)

        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # -- Main window test -----------------------------------
    window = MainWindow()
    test_list = QStandardItemModel(window)
    test_list.setHorizontalHeaderLabels(['Клиент', 'IP Адрес', 'Порт', 'Время подключения'])
    test_list.appendRow([
        QStandardItem('test2'), QStandardItem('192.1686.0.1'), QStandardItem('2551'), QStandardItem('2022.15.23 23:15:10')
    ])
    test_list.appendRow([
        QStandardItem('test3'), QStandardItem('192.1686.0.5'), QStandardItem('8080'), QStandardItem('2022.15.23 23:15:10')
    ])
    window.active_clients_table.setModel(test_list)
    window.active_clients_table.resizeColumnsToContents()

    # -- History window test --------------------------------
    # window = HistoryWindow()
    # test_list = QStandardItemModel(window)
    # test_list.setHorizontalHeaderLabels(['Имя клиента', 'Последний раз входил', 'Отправлено', 'Получено'])
    # test_list.appendRow([
    #     QStandardItem('test2'), QStandardItem('2022.12.15 15:25:10'), QStandardItem('2'), QStandardItem('3')
    # ])
    # test_list.appendRow([
    #     QStandardItem('test3'), QStandardItem('2021.12.15 15:25:10'), QStandardItem('1'), QStandardItem('6')
    # ])
    # window.history_table.setModel(test_list)
    # window.history_table.resizeColumnsToContents()

    # -- Server configuration window ------------------------
    # window = ConfigWindow()

    # -------------------------------------------------------
    app.exec_()
