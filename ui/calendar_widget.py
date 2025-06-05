from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                            QCalendarWidget, QListWidget, QListWidgetItem, QDialog,
                            QComboBox, QDateEdit, QLineEdit, QTextEdit, QMessageBox,
                            QCheckBox, QSpinBox, QGroupBox, QTimeEdit, QFileDialog,
                            QFormLayout)
from PyQt6.QtCore import Qt, QDate, QTimer, QTime
from PyQt6.QtGui import QColor, QTextCharFormat
from core.database import Contract, Property, Payment, Maintenance, PaymentStatus
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import os

class CalendarWidget(QWidget):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.reminder_time = QTime(9, 0)  # По умолчанию напоминания в 9:00
        self.init_ui()
        self.setup_reminders()
        self.update_calendar_colors()

    def init_ui(self):
        # Apply stylesheet from PaymentsWidget
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:checked {
                background-color: #0a3d91;
            }
            QLabel {
                color: #ffffff;
            }
            QComboBox {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow {
                image: url(icons/down_arrow.png); /* placeholder */
            }
            QGroupBox {
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QScrollArea {
                border: none;
                background-color: transparent; /* Это важно для согласованного фона скролл-областей */
            }
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #3d3d3d;
                border: none;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 8px;
                background-color: #2b2b2b; /* Фон обычной строки */
                color: #ffffff;
            }
            QTableWidget::item:selected {
                background-color: #3d3d3d; /* Фон выбранной строки */
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                color: #ffffff;
                padding: 8px;
                border: none;
                border-right: 1px solid #3d3d3d;
                border-bottom: 1px solid #3d3d3d;
                font-weight: bold;
            }
            QListWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #0d47a1;
            }
            QDateEdit {
              background-color: #2b2b2b;
              color: #ffffff;
              border: 1px solid #3d3d3d;
              border-radius: 4px;
              padding: 5px;
          }
           QDateEdit::drop-down {
               subcontrol-origin: padding;
               subcontrol-position: top right;
               width: 20px;
               border-left-width: 1px;
               border-left-color: darkgray;
               border-left-style: solid; /* change to suit you */
               border-top-right-radius: 3px;
               border-bottom-right-radius: 3px;
           }
           QDateEdit::down-arrow {
               image: url(icons/calendar_icon.png); /* placeholder for a calendar icon */
           }
        """)

        layout = QHBoxLayout(self)

        # Левая панель с календарем
        left_panel = QVBoxLayout()
        
        # Календарь
        self.calendar = QCalendarWidget()
        self.calendar.clicked.connect(self.date_selected)
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        left_panel.addWidget(self.calendar)

        # Легенда цветов
        legend_group = QGroupBox("Легенда")
        legend_layout = QVBoxLayout()
        
        # Добавляем элементы легенды
        legend_items = [
            ("Занято", QColor(255, 200, 200)),  # Красный
            ("Свободно", QColor(200, 255, 200)),  # Зеленый
            ("Техобслуживание", QColor(255, 255, 200)),  # Желтый
            ("Срок оплаты", QColor(200, 200, 255)),  # Синий
            ("Окончание договора", QColor(255, 200, 255))  # Фиолетовый
        ]
        
        for text, color in legend_items:
            item = QLabel()
            item.setStyleSheet(f"background-color: {color.name()}; padding: 5px; border-radius: 3px;")
            item.setText(text)
            legend_layout.addWidget(item)
            
        legend_group.setLayout(legend_layout)
        left_panel.addWidget(legend_group)

        # Кнопки управления
        buttons_layout = QHBoxLayout()
        add_event_btn = QPushButton("Добавить событие")
        add_event_btn.clicked.connect(self.show_add_event_dialog)
        buttons_layout.addWidget(add_event_btn)

        export_btn = QPushButton("Экспорт в iCal")
        export_btn.clicked.connect(self.export_to_ical)
        buttons_layout.addWidget(export_btn)

        settings_btn = QPushButton("Настройки")
        settings_btn.clicked.connect(self.show_settings_dialog)
        buttons_layout.addWidget(settings_btn)

        left_panel.addLayout(buttons_layout)

        # Правая панель со списком событий
        right_panel = QVBoxLayout()
        
        # Фильтры
        filter_group = QGroupBox("Фильтры")
        filter_layout = QVBoxLayout()
        
        self.filters = {
            'contract_end': QCheckBox("Окончание договоров"),
            'payment_due': QCheckBox("Сроки оплаты"),
            'maintenance': QCheckBox("Техническое обслуживание")
        }
        
        for checkbox in self.filters.values():
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_events_list)
            filter_layout.addWidget(checkbox)
            
        filter_group.setLayout(filter_layout)
        right_panel.addWidget(filter_group)
        
        right_panel.addWidget(QLabel("События на выбранную дату:"))
        
        self.events_list = QListWidget()
        right_panel.addWidget(self.events_list)

        # Добавляем панели в главный layout
        layout.addLayout(left_panel, 2)
        layout.addLayout(right_panel, 1)

        # Загружаем события на текущую дату
        self.date_selected(self.calendar.selectedDate())

    def setup_reminders(self):
        # Таймер для проверки напоминаний каждую минуту
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)  # 60000 мс = 1 минута

    def check_reminders(self):
        now = datetime.now()
        current_time = QTime(now.hour, now.minute)
        
        # Проверяем, наступило ли время напоминаний
        if current_time.hour() == self.reminder_time.hour() and current_time.minute() == self.reminder_time.minute():
            today = now.date()
            events = self.get_events_for_date(today)
            
            # Показываем уведомления для событий
            for event in events:
                if event['type'] == 'contract_end':
                    QMessageBox.information(self, "Напоминание", 
                        f"Сегодня заканчивается договор №{event['contract_id']} с {event['tenant_name']}")
                elif event['type'] == 'payment_due':
                    QMessageBox.information(self, "Напоминание", 
                        f"Сегодня срок оплаты по договору №{event['contract_id']}. Сумма: {event['amount']:.2f} ₽")
                elif event['type'] == 'maintenance':
                    QMessageBox.information(self, "Напоминание", 
                        f"Сегодня запланировано техническое обслуживание: {event['property_name']}")

    def show_settings_dialog(self):
        dialog = SettingsDialog(self.reminder_time, self)
        if dialog.exec():
            self.reminder_time = dialog.reminder_time

    def export_to_ical(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт календаря",
            "",
            "iCalendar Files (*.ics)"
        )
        
        if file_name:
            cal = Calendar()
            cal.add('prodid', '-//Rental System Calendar//')
            cal.add('version', '2.0')

            # Получаем все события за последние 30 дней и следующие 365 дней
            start_date = datetime.now().date() - timedelta(days=30)
            end_date = datetime.now().date() + timedelta(days=365)

            # Экспортируем события
            for date in (start_date + timedelta(n) for n in range((end_date - start_date).days)):
                events = self.get_events_for_date(date)
                for event in events:
                    ical_event = Event()
                    ical_event.add('summary', event['title'])
                    ical_event.add('description', event['description'])
                    ical_event.add('dtstart', date)
                    ical_event.add('dtend', date)
                    
                    # Добавляем напоминание
                    ical_event.add('alarm', {
                        'action': 'DISPLAY',
                        'trigger': timedelta(days=-1)  # За день до события
                    })
                    
                    cal.add_component(ical_event)

            # Сохраняем файл
            with open(file_name, 'wb') as f:
                f.write(cal.to_ical())
            
            QMessageBox.information(self, "Успех", "Календарь успешно экспортирован")

    def get_events_for_date(self, date):
        events = []

        # Проверяем окончание договоров
        expiring_contracts = self.session.query(Contract).filter(
            Contract.end_date == date
        ).all()
        for contract in expiring_contracts:
            events.append({
                'type': 'contract_end',
                'contract_id': contract.id,
                'tenant_name': contract.tenant.name,
                'title': f"Окончание договора №{contract.id}",
                'description': f"Договор с {contract.tenant.name} заканчивается"
            })

        # Проверяем сроки оплаты
        due_payments = self.session.query(Payment).filter(
            Payment.due_date == date
        ).all()
        for payment in due_payments:
            # Проверяем, существует ли связанный договор
            if payment.contract:
                events.append({
                    'type': 'payment_due',
                    'contract_id': payment.contract.id,
                    'amount': payment.amount,
                    'title': f"Срок оплаты по договору №{payment.contract.id}",
                    'description': f"Сумма: {payment.amount:.2f} ₽"
                })
            else:
                # Обрабатываем случай удаленного договора
                events.append({
                    'type': 'payment_due',
                    'contract_id': None,
                    'amount': payment.amount,
                    'title': "Срок оплаты (договор удален)",
                    'description': f"Сумма: {payment.amount:.2f} ₽"
                })

        # Проверяем техническое обслуживание
        maintenance = self.session.query(Maintenance).filter(
            Maintenance.date == date
        ).all()
        for maint in maintenance:
            events.append({
                'type': 'maintenance',
                'property_name': maint.property.name,
                'title': f"Техническое обслуживание: {maint.property.name}",
                'description': maint.description
            })

        return events

    def date_selected(self, date):
        self.update_events_list()

    def update_events_list(self):
        self.events_list.clear()
        selected_date = self.calendar.selectedDate().toPyDate()
        events = self.get_events_for_date(selected_date)

        # Фильтруем события
        filtered_events = [
            event for event in events 
            if self.filters[event['type']].isChecked()
        ]

        # Отображаем события в списке
        for event in filtered_events:
            item = QListWidgetItem()
            item.setText(f"{event['title']}\n{event['description']}")
            
            # Устанавливаем цвет в зависимости от типа события
            if event['type'] == 'contract_end':
                item.setBackground(QColor(255, 200, 200))  # Красный
            elif event['type'] == 'payment_due':
                item.setBackground(QColor(255, 255, 200))  # Желтый
            elif event['type'] == 'maintenance':
                item.setBackground(QColor(200, 255, 200))  # Зеленый
            
            self.events_list.addItem(item)

    def show_add_event_dialog(self):
        dialog = AddEventDialog(self.session)
        if dialog.exec():
            self.update_events_list()

    def update_calendar_colors(self):
        """Обновляет цвета в календаре на основе статусов объектов и событий"""
        # Получаем все даты в текущем месяце
        current_date = self.calendar.selectedDate()
        first_day = QDate(current_date.year(), current_date.month(), 1)
        last_day = QDate(current_date.year(), current_date.month(), current_date.daysInMonth())
        
        # Получаем все договоры и их даты
        contracts = self.session.query(Contract).all()
        for contract in contracts:
            start_date = contract.start_date
            end_date = contract.end_date
            
            # Если договор активен в текущем месяце
            if (start_date <= last_day.toPyDate() and end_date >= first_day.toPyDate()):
                # Получаем даты для окраски
                color_start = max(start_date, first_day.toPyDate())
                color_end = min(end_date, last_day.toPyDate())
                
                # Окрашиваем даты в календаре
                current = color_start
                while current <= color_end:
                    qdate = QDate(current.year, current.month, current.day)
                    self.calendar.setDateTextFormat(qdate, self.get_date_format('occupied'))
                    current += timedelta(days=1)
        
        # Получаем все даты технического обслуживания
        maintenance_dates = self.session.query(Maintenance.date).all()
        for date in maintenance_dates:
            qdate = QDate(date[0].year, date[0].month, date[0].day)
            if first_day <= qdate <= last_day:
                self.calendar.setDateTextFormat(qdate, self.get_date_format('maintenance'))
        
        # Получаем все даты платежей
        payment_dates = self.session.query(Payment.due_date).all()
        for date in payment_dates:
            qdate = QDate(date[0].year, date[0].month, date[0].day)
            if first_day <= qdate <= last_day:
                self.calendar.setDateTextFormat(qdate, self.get_date_format('payment'))

    def get_date_format(self, status):
        """Возвращает формат даты для календаря в зависимости от статуса"""
        format = QTextCharFormat()
        
        if status == 'occupied':
            format.setBackground(QColor(255, 200, 200))  # Красный
        elif status == 'available':
            format.setBackground(QColor(200, 255, 200))  # Зеленый
        elif status == 'maintenance':
            format.setBackground(QColor(255, 255, 200))  # Желтый
        elif status == 'payment':
            format.setBackground(QColor(200, 200, 255))  # Синий
        elif status == 'contract_end':
            format.setBackground(QColor(255, 200, 255))  # Фиолетовый
            
        return format

class SettingsDialog(QDialog):
    def __init__(self, current_time, notification_manager):
        super().__init__()
        self.reminder_time = current_time
        self.notification_manager = notification_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Настройки календаря и уведомлений")
        layout = QVBoxLayout(self)

        # Время напоминаний
        time_group = QGroupBox("Время напоминаний")
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Время напоминаний:"))
        self.time_edit = QTimeEdit(self.reminder_time)
        time_layout.addWidget(self.time_edit)
        time_group.setLayout(time_layout)
        layout.addWidget(time_group)

        # Настройки уведомлений
        notification_group = QGroupBox("Настройки уведомлений")
        notification_layout = QVBoxLayout()

        # Всплывающие уведомления
        self.enable_popup = QCheckBox("Включить всплывающие уведомления")
        self.enable_popup.setChecked(self.notification_manager.settings['reminders']['enable_popup'])
        notification_layout.addWidget(self.enable_popup)

        # Звуковые уведомления
        self.enable_sound = QCheckBox("Включить звуковые уведомления")
        self.enable_sound.setChecked(self.notification_manager.settings['reminders']['enable_sound'])
        notification_layout.addWidget(self.enable_sound)

        # Email уведомления
        self.enable_email = QCheckBox("Включить email уведомления")
        self.enable_email.setChecked(self.notification_manager.settings['reminders']['enable_email'])
        notification_layout.addWidget(self.enable_email)

        # Дни для напоминаний
        days_group = QGroupBox("Дни для напоминаний")
        days_layout = QFormLayout()

        # Платежи
        self.payment_days = QLineEdit()
        self.payment_days.setText(','.join(map(str, self.notification_manager.settings['reminders']['payment_days'])))
        days_layout.addRow("Дни до платежа:", self.payment_days)

        # Договоры
        self.contract_days = QLineEdit()
        self.contract_days.setText(','.join(map(str, self.notification_manager.settings['reminders']['contract_days'])))
        days_layout.addRow("Дни до окончания договора:", self.contract_days)

        # Техобслуживание
        self.maintenance_days = QLineEdit()
        self.maintenance_days.setText(','.join(map(str, self.notification_manager.settings['reminders']['maintenance_days'])))
        days_layout.addRow("Дни до техобслуживания:", self.maintenance_days)

        days_group.setLayout(days_layout)
        notification_layout.addWidget(days_group)

        notification_group.setLayout(notification_layout)
        layout.addWidget(notification_group)

        # Кнопки
        buttons = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def save_settings(self):
        # Сохраняем время напоминаний
        self.reminder_time = self.time_edit.time()

        # Сохраняем настройки уведомлений
        new_settings = {
            'reminders': {
                'enable_popup': self.enable_popup.isChecked(),
                'enable_sound': self.enable_sound.isChecked(),
                'enable_email': self.enable_email.isChecked(),
                'payment_days': [int(x.strip()) for x in self.payment_days.text().split(',')],
                'contract_days': [int(x.strip()) for x in self.contract_days.text().split(',')],
                'maintenance_days': [int(x.strip()) for x in self.maintenance_days.text().split(',')],
                'notification_time': self.reminder_time.toString('HH:mm')
            }
        }

        # Обновляем настройки в менеджере уведомлений
        self.notification_manager.update_settings(new_settings)
        self.accept()

class AddEventDialog(QDialog):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Добавить событие")
        layout = QVBoxLayout(self)

        # Тип события
        self.event_type = QComboBox()
        self.event_type.addItems([
            "Техническое обслуживание",
            "Срок оплаты",
            "Окончание договора"
        ])
        layout.addWidget(QLabel("Тип события:"))
        layout.addWidget(self.event_type)

        # Дата события
        self.event_date = QDateEdit()
        self.event_date.setDate(QDate.currentDate())
        layout.addWidget(QLabel("Дата события:"))
        layout.addWidget(self.event_date)

        # Объект (для технического обслуживания)
        self.property_combo = QComboBox()
        properties = self.session.query(Property).all()
        for property in properties:
            self.property_combo.addItem(property.name, property.id)
        layout.addWidget(QLabel("Объект:"))
        layout.addWidget(self.property_combo)

        # Договор (для платежей и окончания)
        self.contract_combo = QComboBox()
        contracts = self.session.query(Contract).all()
        for contract in contracts:
            self.contract_combo.addItem(f"Договор №{contract.id}", contract.id)
        layout.addWidget(QLabel("Договор:"))
        layout.addWidget(self.contract_combo)

        # Описание
        self.description = QTextEdit()
        layout.addWidget(QLabel("Описание:"))
        layout.addWidget(self.description)

        # Кнопки
        buttons = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_event)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def save_event(self):
        event_type = self.event_type.currentText()
        date = self.event_date.date().toPyDate()

        if event_type == "Техническое обслуживание":
            maintenance = Maintenance(
                property_id=self.property_combo.currentData(),
                date=date,
                description=self.description.toPlainText()
            )
            self.session.add(maintenance)
        elif event_type == "Срок оплаты":
            payment = Payment(
                contract_id=self.contract_combo.currentData(),
                due_date=date,
                amount=0,  # Сумма будет установлена позже
                status=PaymentStatus.PENDING
            )
            self.session.add(payment)
        elif event_type == "Окончание договора":
            contract = self.session.query(Contract).get(self.contract_combo.currentData())
            if contract:
                contract.end_date = date

        self.session.commit()
        self.accept() 