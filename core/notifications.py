from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon
from core.database import Payment, Contract, Property, PaymentStatus, Maintenance
from datetime import datetime, timedelta
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationManager(QObject):
    # Сигналы для различных типов уведомлений
    payment_reminder = pyqtSignal(str, str)  # title, message
    contract_expiry = pyqtSignal(str, str)   # title, message
    maintenance_reminder = pyqtSignal(str, str)  # title, message

    def __init__(self, session):
        super().__init__()
        self.session = session
        self.settings = self.load_settings()
        self.init_tray()
        self.init_timers()
        self.check_notifications()

    def init_tray(self):
        self.tray = QSystemTrayIcon()
        # Используем относительный путь к иконке
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'icon.png')
        if os.path.exists(icon_path):
            self.tray.setIcon(QIcon(icon_path))
        else:
            # Если иконка не найдена, создаем пустую иконку
            self.tray.setIcon(QIcon())
        
        # Создаем меню для трея
        menu = QMenu()
        show_action = menu.addAction("Показать")
        show_action.triggered.connect(self.show_notification)
        exit_action = menu.addAction("Выход")
        exit_action.triggered.connect(self.exit_app)
        
        self.tray.setContextMenu(menu)
        self.tray.show()

    def init_timers(self):
        # Таймер для проверки платежей (каждый час)
        self.payment_timer = QTimer()
        self.payment_timer.timeout.connect(self.check_payments)
        self.payment_timer.start(3600000)  # 1 час

        # Таймер для проверки договоров (раз в день)
        self.contract_timer = QTimer()
        self.contract_timer.timeout.connect(self.check_contracts)
        self.contract_timer.start(86400000)  # 24 часа

        # Таймер для проверки техобслуживания (раз в день)
        self.maintenance_timer = QTimer()
        self.maintenance_timer.timeout.connect(self.check_maintenance)
        self.maintenance_timer.start(86400000)  # 24 часа

    def load_settings(self):
        try:
            with open('notification_settings.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'email': {
                    'enabled': False,
                    'smtp_server': '',
                    'port': 587,
                    'username': '',
                    'password': ''
                },
                'reminders': {
                    'payment_days': [3, 1],  # дни до платежа для напоминания
                    'contract_days': [30, 7, 1],  # дни до окончания договора
                    'maintenance_days': [7, 1],  # дни до техобслуживания
                    'notification_time': '09:00',  # время отправки уведомлений
                    'enable_sound': True,  # включить звуковые уведомления
                    'enable_popup': True,  # включить всплывающие уведомления
                    'enable_email': False  # включить email уведомления
                }
            }

    def save_settings(self):
        with open('notification_settings.json', 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    def check_notifications(self):
        self.check_payment_reminders()
        self.check_contract_expiry()
        self.check_maintenance()

    def check_payment_reminders(self):
        # Проверяем платежи, срок оплаты которых наступает через 3 дня
        three_days_later = datetime.now().date() + timedelta(days=3)
        upcoming_payments = self.session.query(Payment).filter(
            Payment.due_date == three_days_later,
            Payment.status == PaymentStatus.PENDING
        ).all()

        for payment in upcoming_payments:
            title = "Напоминание об оплате"
            message = f"Через 3 дня наступает срок оплаты по договору №{payment.contract.id}. " \
                     f"Сумма: {payment.amount:.2f} ₽"
            self.payment_reminder.emit(title, message)

    def check_contract_expiry(self):
        # Проверяем договоры, которые истекают через 30 дней
        thirty_days_later = datetime.now().date() + timedelta(days=30)
        expiring_contracts = self.session.query(Contract).filter(
            Contract.end_date == thirty_days_later,
            Contract.status == 'active'
        ).all()

        for contract in expiring_contracts:
            title = "Истечение договора"
            message = f"Договор №{contract.id} с {contract.tenant.name} истекает через 30 дней"
            self.contract_expiry.emit(title, message)

    def check_maintenance(self):
        # Проверяем необходимость технического обслуживания
        properties = self.session.query(Property).filter(
            Property.status == 'maintenance'
        ).all()

        for property in properties:
            title = "Техническое обслуживание"
            message = f"Требуется техническое обслуживание объекта: {property.name}"
            self.maintenance_reminder.emit(title, message)

    def check_payments(self):
        today = datetime.now().date()
        
        # Получаем все ожидающие платежи
        payments = self.session.query(Payment).filter(
            Payment.status == PaymentStatus.PENDING
        ).all()

        for payment in payments:
            days_until_due = (payment.due_date - today).days
            
            # Проверяем, нужно ли отправить напоминание
            if days_until_due in self.settings['reminders']['payment_days']:
                message = f"Напоминание: платеж по договору №{payment.contract.id} " \
                         f"на сумму {payment.amount} руб. должен быть оплачен через {days_until_due} дней"
                
                # Отправляем уведомление
                if self.settings['reminders']['enable_popup']:
                    self.payment_reminder.emit("Напоминание о платеже", message)
                
                # Отправляем email если включено
                if self.settings['reminders']['enable_email'] and self.settings['email']['enabled']:
                    self.send_email(
                        payment.contract.tenant.contact_info,
                        "Напоминание о платеже",
                        message
                    )

    def check_contracts(self):
        today = datetime.now().date()
        
        # Получаем все активные договоры
        contracts = self.session.query(Contract).filter(
            Contract.status == 'active'
        ).all()

        for contract in contracts:
            days_until_end = (contract.end_date - today).days
            
            # Проверяем, нужно ли отправить уведомление
            if days_until_end in self.settings['reminders']['contract_days']:
                message = f"Договор №{contract.id} с {contract.tenant.name} " \
                         f"истекает через {days_until_end} дней"
                
                # Отправляем уведомление
                if self.settings['reminders']['enable_popup']:
                    self.contract_expiry.emit("Окончание договора", message)
                
                # Отправляем email если включено
                if self.settings['reminders']['enable_email'] and self.settings['email']['enabled']:
                    self.send_email(
                        contract.tenant.contact_info,
                        "Окончание договора",
                        message
                    )

    def check_maintenance(self):
        today = datetime.now().date()
        
        # Получаем все запланированные работы
        maintenance = self.session.query(Maintenance).filter(
            Maintenance.status == 'planned'
        ).all()

        for record in maintenance:
            days_until_maintenance = (record.date - today).days
            
            # Проверяем, нужно ли отправить напоминание
            if days_until_maintenance in self.settings['reminders']['maintenance_days']:
                message = f"Напоминание: техобслуживание помещения {record.property.name} " \
                         f"запланировано через {days_until_maintenance} дней"
                
                # Отправляем уведомление
                if self.settings['reminders']['enable_popup']:
                    self.maintenance_reminder.emit("Техобслуживание", message)
                
                # Отправляем email если включено
                if self.settings['reminders']['enable_email'] and self.settings['email']['enabled']:
                    self.send_email(
                        "admin@example.com",  # Замените на реальный email администратора
                        "Техобслуживание",
                        message
                    )

    def send_email(self, to_email, subject, message):
        if not self.settings['email']['enabled']:
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = self.settings['email']['username']
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            with smtplib.SMTP(self.settings['email']['smtp_server'], self.settings['email']['port']) as server:
                server.starttls()
                server.login(self.settings['email']['username'], self.settings['email']['password'])
                server.send_message(msg)
        except Exception as e:
            print(f"Ошибка отправки email: {str(e)}")

    def show_notification(self, title, message):
        if self.settings['reminders']['enable_popup']:
            self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)
        
        if self.settings['reminders']['enable_sound']:
            # Здесь можно добавить воспроизведение звука
            pass

    def exit_app(self):
        self.tray.hide()
        QApplication.quit()

    def update_settings(self, new_settings):
        """Обновляет настройки уведомлений"""
        self.settings.update(new_settings)
        self.save_settings()
        
        # Перезапускаем таймеры с новыми настройками
        self.init_timers() 