from PyQt5.QtWidgets import QDialog, QPushButton, QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


class StatWindow(QDialog):
    """ Class to work with users statistics """

    def __init__(self, database):
        super().__init__()

        self.db = database
        self.initUI()

    def initUI(self):
        # -- Window settings -------------------------------
        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # -- Close window button ---------------------------
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        # -- Statistics list table -------------------------
        self.stat_table = QTableView(self)
        self.stat_table.setFixedSize(580, 620)
        self.stat_table.move(10, 10)

        self.create_stat_model()

    def create_stat_model(self):
        """ Create statistics window and fill in the user statistics table """
        hist_list = self.db.message_history()

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

        self.stat_table.setModel(table)
        self.stat_table.resizeColumnsToContents()
        self.stat_table.resizeRowsToContents()
