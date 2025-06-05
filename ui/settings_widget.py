from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Настройки приложения"))

        # Язык интерфейса
        layout.addWidget(QLabel("Язык интерфейса:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Русский", "English"])
        layout.addWidget(self.lang_combo)

        # Резервное копирование
        backup_btn = QPushButton("Сделать резервную копию базы данных")
        backup_btn.clicked.connect(self.backup_db)
        layout.addWidget(backup_btn)

        # Управление пользователями (заглушка)
        users_btn = QPushButton("Управление пользователями (роль/доступ)")
        users_btn.clicked.connect(self.manage_users)
        layout.addWidget(users_btn)

        layout.addStretch()

    def backup_db(self):
        QMessageBox.information(self, "Резервное копирование", "Функция резервного копирования будет реализована позже.")

    def manage_users(self):
        QMessageBox.information(self, "Пользователи", "Система ролей и управления пользователями будет реализована позже.") 