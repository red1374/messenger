import os
import sys

from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QLabel, QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer

sys.path.append(os.path.join(os.getcwd(), '..'))

from server.stat_window import StatWindow
from server.config_window import ConfigWindow
from server.add_user import RegisterUser
from server.remove_user import DelUserDialog


class MainWindow(QMainWindow):
    """Server main window class"""
    def __init__(self, database, server, config):
        """Setting up server main window and all controls parameters"""
        super().__init__()

        self.db = database

        self.server_thread = server
        self.config = config

        # Exit menu item
        self.exitAction = QAction('Выход', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(qApp.quit)

        # Refresh a list
        self.refresh_button = QAction('Обновить список', self)

        # Show users login history
        self.show_history_button = QAction('История клиентов', self)

        # Show config window
        self.config_button = QAction('Настройки', self)

        # Register new user
        self.register_button = QAction('Регистрация пользователя', self)

        # Remove user button
        self.remove_button = QAction('Удаление пользователя', self)

        self.statusBar()
        self.statusBar().showMessage('Server is working')

        # Toolbar
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_button)
        self.toolbar.addAction(self.register_button)
        self.toolbar.addAction(self.remove_button)

        # Main window settings
        self.setWindowTitle('Сервер сообщений v1.2')
        self.setFixedSize(800, 600)

        self.label = QLabel('Список подключенных клиентов:', self)
        self.label.setFixedSize(400, 15)
        self.label.move(10, 35)

        # Connected users table
        self.active_clients_table = QTableView(self)
        self.active_clients_table.setFixedSize(780, 400)
        self.active_clients_table.move(10, 55)

        # -- Create active users list update timer ---------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_active_users_list)
        self.timer.start(1000)

        # -- Bind main window menu items with functions ----------
        self.refresh_button.triggered.connect(self.update_active_users_list)
        self.show_history_button.triggered.connect(self.show_statistics)
        self.config_button.triggered.connect(self.server_config)
        self.register_button.triggered.connect(self.register_user)
        self.remove_button.triggered.connect(self.delete_user)

        self.show()

    def get_active_users_model(self):
        """Creating active users list table method"""
        users_list = self.db.active_users_list()
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

    def update_active_users_list(self):
        """Updating active users list table if new client connected method"""

        self.active_clients_table.setModel(self.get_active_users_model())
        self.active_clients_table.resizeColumnsToContents()
        self.active_clients_table.resizeRowsToContents()

    def show_statistics(self):
        """Creating user statistics window method"""
        global stat_window
        stat_window = StatWindow(self.db)
        stat_window.show()

    def server_config(self):
        """Creating server configuration window method"""

        global config_window

        config_window = ConfigWindow(self.config)

    def register_user(self):
        """Creating user registration window method"""
        global reg_window

        reg_window = RegisterUser(self.db, self.server_thread)
        reg_window.show()

    def delete_user(self):
        """Creating user delete window method"""
        global rem_window

        rem_window = DelUserDialog(self.db, self.server_thread)
        rem_window.show()
