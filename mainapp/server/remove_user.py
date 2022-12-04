from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton
from PyQt5.QtCore import Qt


class DelUserDialog(QDialog):
    """Delete user dialog window class"""
    def __init__(self, database, server):
        super().__init__()
        self.db = database
        self.server = server

        # -- Window settings ----------------------------
        self.setWindowTitle('Удаление пользователя')
        self.setFixedSize(350, 120)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        # -- Select user field label --------------------
        self.selector_label = QLabel(
            'Выберите пользователя:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        # -- Select user field --------------------------
        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_ok = QPushButton('Удалить', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)
        self.btn_ok.clicked.connect(self.remove_user)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.all_users_fill()

    def all_users_fill(self):
        """Users fill in the field method"""
        self.selector.addItems([item[0] for item in self.db.users_list()])

    def remove_user(self):
        """Delete user handler method"""
        self.db.remove_user(self.selector.currentText())
        if self.selector.currentText() in self.server.clients_names:
            sock = self.server.clients_names[self.selector.currentText()]
            del self.server.clients_names[self.selector.currentText()]
            self.server.remove_client(sock)

        # -- Send signals to clients fo users list update ----------
        self.server.service_update_lists()
        self.close()
