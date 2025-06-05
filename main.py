import sys
import os
os.environ['QT_API'] = 'pyqt6'
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                            QFrame, QStyle, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor
from sqlalchemy.orm import sessionmaker
import qdarkstyle
from core.database import init_db, Session
from ui.property_widget import PropertyWidget
from ui.contract_widget import ContractWidget
from ui.payments_widget import PaymentsWidget
from ui.documents_widget import DocumentsWidget
from ui.reports_widget import ReportsWidget
from ui.analytics_widget import AnalyticsWidget
from ui.tenants_widget import TenantsWidget
from core.notifications import NotificationManager
from ui.calendar_widget import CalendarWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.session = Session(bind=init_db())
        self.init_ui()
        self.init_notifications()

    def init_ui(self):
        self.setWindowTitle("Система управления арендой")
        self.setMinimumSize(1200, 800)

        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Главный layout
        layout = QHBoxLayout(central_widget)

        # Левая панель с кнопками
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        left_panel.setContentsMargins(10, 10, 10, 10)

        # Стили для кнопок
        button_style = """
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 10px;
                text-align: left;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:checked {
                background-color: #0a3d91;
            }
        """

        # Кнопки навигации
        self.nav_buttons = {}
        nav_items = [
            ("Объекты", self.show_properties),
            ("Договоры", self.show_contracts),
            ("Платежи", self.show_payments),
            ("Арендаторы", self.show_tenants),
            ("Документы", self.show_documents),
            ("Отчеты", self.show_reports),
            ("Аналитика", self.show_analytics),
            ("Календарь", self.show_calendar)
        ]

        for text, callback in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(callback)
            self.nav_buttons[text] = btn
            left_panel.addWidget(btn)

        left_panel.addStretch()
        layout.addLayout(left_panel)

        # Правая панель с контентом
        self.content_area = QStackedWidget()
        layout.addWidget(self.content_area, 1)

        # Инициализация виджетов
        self.properties_widget = PropertyWidget(self.session)
        self.contracts_widget = ContractWidget(self.session)
        self.payments_widget = PaymentsWidget(self.session)
        self.tenants_widget = TenantsWidget(self.session)
        self.documents_widget = DocumentsWidget(self.session)
        self.reports_widget = ReportsWidget(self.session)
        self.analytics_widget = AnalyticsWidget(self.session)
        self.calendar_widget = CalendarWidget(self.session)

        # Добавляем виджеты в стек
        self.content_area.addWidget(self.properties_widget)
        self.content_area.addWidget(self.contracts_widget)
        self.content_area.addWidget(self.payments_widget)
        self.content_area.addWidget(self.tenants_widget)
        self.content_area.addWidget(self.documents_widget)
        self.content_area.addWidget(self.reports_widget)
        self.content_area.addWidget(self.analytics_widget)
        self.content_area.addWidget(self.calendar_widget)

        # Показываем приветственное сообщение
        welcome = QWidget()
        welcome_layout = QVBoxLayout(welcome)
        welcome_label = QLabel("Добро пожаловать в систему управления арендой")
        welcome_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
                padding: 20px;
            }
        """)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        self.content_area.addWidget(welcome)

    def init_notifications(self):
        self.notification_manager = NotificationManager(self.session)
        
        # Подключаем сигналы уведомлений
        self.notification_manager.payment_reminder.connect(self.show_notification)
        self.notification_manager.contract_expiry.connect(self.show_notification)
        self.notification_manager.maintenance_reminder.connect(self.show_notification)

        # Передаем менеджер уведомлений в календарь
        self.calendar_widget.notification_manager = self.notification_manager

    def show_notification(self, title, message):
        QMessageBox.information(self, title, message)

    def _set_active_button(self, button_name):
        for name, button in self.nav_buttons.items():
            button.setChecked(name == button_name)

    def show_properties(self):
        self._set_active_button("Объекты")
        self.content_area.setCurrentWidget(self.properties_widget)

    def show_contracts(self):
        self._set_active_button("Договоры")
        self.content_area.setCurrentWidget(self.contracts_widget)

    def show_payments(self):
        self._set_active_button("Платежи")
        self.content_area.setCurrentWidget(self.payments_widget)

    def show_tenants(self):
        self._set_active_button("Арендаторы")
        self.content_area.setCurrentWidget(self.tenants_widget)

    def show_documents(self):
        self._set_active_button("Документы")
        self.content_area.setCurrentWidget(self.documents_widget)

    def show_reports(self):
        self._set_active_button("Отчеты")
        self.content_area.setCurrentWidget(self.reports_widget)

    def show_analytics(self):
        self._set_active_button("Аналитика")
        self.content_area.setCurrentWidget(self.analytics_widget)

    def show_calendar(self):
        self._set_active_button("Календарь")
        self.content_area.setCurrentWidget(self.calendar_widget)

def main():
    app = QApplication(sys.argv)
    # Применяем темную тему
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 