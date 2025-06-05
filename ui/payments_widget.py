import os # Assuming os is needed based on previous PropertyWidget changes, add if not present
import shutil # Assuming shutil is needed based on previous PropertyWidget changes, add if not present
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                            QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
                            QFormLayout, QLineEdit, QTextEdit, QComboBox, QDateEdit, QDoubleSpinBox, QGroupBox, QScrollArea)
from PyQt6.QtCore import Qt, QDate, QTimer # Import QTimer
from PyQt6.QtGui import QColor, QDoubleValidator
from core.database import Payment, Contract, PaymentStatus, ContractStatus
from sqlalchemy.orm import Session
from datetime import datetime

class PaymentsWidget(QWidget):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.init_ui()
        self.load_payments()

    def init_ui(self):
        # Apply dark theme stylesheet to the widget
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
        """)

        layout = QVBoxLayout(self)

        # Верхняя панель с элементами управления
        controls = QHBoxLayout()
        add_btn = QPushButton("Добавить платеж")
        add_btn.clicked.connect(self.show_add_payment_dialog)
        controls.addWidget(add_btn)
       
        edit_btn = QPushButton("Редактировать платеж")
        edit_btn.clicked.connect(self.edit_payment)
        controls.addWidget(edit_btn)

        delete_btn = QPushButton("Удалить платеж")
        delete_btn.clicked.connect(self.delete_payment)
        controls.addWidget(delete_btn)

        controls.addStretch()
        layout.addLayout(controls)

        # Таблица платежей
        self.table = QTableWidget()
        self.table.setStyleSheet("""
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
        """)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Договор", "Сумма", "Дата платежа", "Срок оплаты", "Статус", "Комментарий"
        ])
        layout.addWidget(self.table)

    def load_payments(self):
        self.table.setRowCount(0) # Очищаем таблицу перед загрузкой
        payments = self.session.query(Payment).all()
        self.table.setRowCount(len(payments))
        for row, payment in enumerate(payments):
            self.table.setItem(row, 0, QTableWidgetItem(str(payment.id)))
            
            # Проверяем существование договора
            contract_info = f"Договор №{payment.contract.id}" if payment.contract else "Договор удален"
            self.table.setItem(row, 1, QTableWidgetItem(contract_info))
            
            self.table.setItem(row, 2, QTableWidgetItem(f"{payment.amount:.2f} руб."))
            self.table.setItem(row, 3, QTableWidgetItem(payment.due_date.strftime("%d.%m.%Y")))
            
            # Проверяем дату платежа
            payment_date = payment.payment_date.strftime("%d.%m.%Y") if payment.payment_date else "Не оплачен"
            self.table.setItem(row, 4, QTableWidgetItem(payment_date))
            
            # Статус платежа
            # Удаляем цвет фона для статуса, чтобы соответствовать дизайну арендаторов
            self.table.setItem(row, 5, QTableWidgetItem(payment.status.value))
            
            # Описание
            self.table.setItem(row, 6, QTableWidgetItem(payment.description or ""))

            # Обновляем статус контракта на основе платежей
            if payment.contract:  # Проверяем существование договора
                contract = payment.contract
                all_payments = self.session.query(Payment).filter(Payment.contract_id == contract.id).all()
                has_overdue = any(p.status == PaymentStatus.OVERDUE for p in all_payments)
                has_pending = any(p.status == PaymentStatus.PENDING for p in all_payments)
                
                if has_overdue:
                    contract.status = ContractStatus.ACTIVE  # Если есть просроченные платежи, договор все еще Активен
                elif has_pending:
                    contract.status = ContractStatus.ACTIVE
                else:
                    contract.status = ContractStatus.EXPIRED # Если нет ни просроченных, ни ожидающих
                
                self.session.commit() # Сохраняем изменение статуса контракта
        
        self.table.resizeColumnsToContents() # Устанавливаем эту строку здесь

    def show_add_payment_dialog(self):
        dialog = PaymentDialog(self.session, parent=self) # Для добавления, payment=None по умолчанию
        if dialog.exec():
            # Получаем данные из диалога и создаем новый платеж
            try:
                payment_data = dialog.get_payment_data()
                payment = Payment(
                    contract_id=payment_data['contract_id'],
                    amount=payment_data['amount'],
                    due_date=payment_data['due_date'],
                    payment_date=payment_data['payment_date'],
                    status=payment_data['status'],
                    description=payment_data['description']
                )
                self.session.add(payment)
                self.session.commit()
                self.load_payments()
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка ввода", str(e))

    def edit_payment(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            payment_id = int(self.table.item(current_row, 0).text())
            payment = self.session.query(Payment).get(payment_id)
            if payment:
                dialog = PaymentDialog(self.session, payment=payment, parent=self) # Для редактирования, передаем объект payment
                if dialog.exec():
                    # Получаем обновленные данные из диалога и сохраняем изменения
                    try:
                        payment_data = dialog.get_payment_data()
                        # Обновляем поля существующего объекта payment
                        # payment.contract_id = payment_data['contract_id'] # Нельзя менять договор при редактировании
                        payment.amount = payment_data['amount']
                        payment.due_date = payment_data['due_date']
                        payment.payment_date = payment_data['payment_date']
                        payment.status = payment_data['status']
                        payment.description = payment_data['description']
                        self.session.commit()
                        self.load_payments()
                    except ValueError as e:
                        QMessageBox.warning(self, "Ошибка ввода", str(e))

    def delete_payment(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            payment_id = int(self.table.item(current_row, 0).text())
            payment = self.session.query(Payment).get(payment_id)
            if payment:
                reply = QMessageBox.question(
                    self,
                    "Подтверждение",
                    "Вы уверены, что хотите удалить этот платеж?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.session.delete(payment)
                    self.session.commit()
                    self.load_payments()

class PaymentDialog(QDialog):
    def __init__(self, session: Session, *, payment: Payment = None, parent=None): # session - обязательный позиционный, payment и parent - необязательные ключевые
        super().__init__(parent) # Передаем parent в конструктор QDialog
        self.session = session
        self.payment = payment # Сохраняем объект платежа для редактирования
        
        # Add debug print to check session type in __init__
        print(f"[DEBUG] PaymentDialog.__init__ self.session type: {type(self.session)}")

        # Defer init_ui call to allow object to be fully constructed
        QTimer.singleShot(0, self.init_ui)

        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {
                border: 1px solid #0d47a1;
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
        # If передан объект платежа, заполняем поля (This logic will now be called after deferred init_ui)
        # No, this logic should be called after init_ui in the deferred call as well
        # if self.payment:
        #     self.populate_fields()

    def init_ui(self):
        # Add debug print to check session type at start of init_ui
        print(f"[DEBUG] PaymentDialog.init_ui start self.session type: {type(self.session)}")

        self.setWindowTitle("Добавить платеж" if self.payment is None else f"Редактировать платеж №{self.payment.id}") # Меняем заголовок с ID
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Выбор договора
        self.contract_combo = QComboBox()
        contracts = self.session.query(Contract).all()
        for contract in contracts:
            # Убедимся, что contract.id не None перед добавлением
            if contract.id is not None:
                # Добавляем информацию об имуществе в комбобокс договора
                property_info = contract.property.name if contract.property else 'Нет имущества'
                self.contract_combo.addItem(f"Договор №{contract.id} ({property_info})", contract.id)
       
        # Отключаем комбобокс при редактировании
        if self.payment:
            self.contract_combo.setEnabled(False)

        layout.addWidget(QLabel("Договор:"))
        layout.addWidget(self.contract_combo)

        # Сумма
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("Введите сумму")
        # Добавим валидатор для чисел
        # from PyQt6.QtGui import QDoubleValidator # Импортирован в начале файла
        validator = QDoubleValidator(0.00, 1000000.00, 2)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.amount_edit.setValidator(validator)
        
        layout.addWidget(QLabel("Сумма:"))
        layout.addWidget(self.amount_edit)

        # Дата платежа
        self.payment_date = QDateEdit()
        self.payment_date.setDate(QDate.currentDate())
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDisplayFormat("dd.MM.yyyy")
        layout.addWidget(QLabel("Дата платежа:"))
        layout.addWidget(self.payment_date)

        # Срок оплаты
        self.due_date = QDateEdit()
        self.due_date.setDate(QDate.currentDate())
        self.due_date.setCalendarPopup(True)
        self.due_date.setDisplayFormat("dd.MM.yyyy")
        layout.addWidget(QLabel("Срок оплаты:"))
        layout.addWidget(self.due_date)

        # Статус
        self.status_combo = QComboBox()
        self.status_combo.addItems([status.value for status in PaymentStatus])
       
        # Отключаем выбор статуса при добавлении нового платежа, статус определяется автоматически по дате
        if not self.payment:
            self.status_combo.setEnabled(False)
        else:
             # При редактировании статус можно менять, но текущий статус должен быть выбран
             if self.payment.status:
                 index = self.status_combo.findText(self.payment.status.value)
                 if index != -1:
                     self.status_combo.setCurrentIndex(index)

        layout.addWidget(QLabel("Статус:"))
        layout.addWidget(self.status_combo)

        # Комментарий
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Введите комментарий")
        layout.addWidget(QLabel("Комментарий:"))
        layout.addWidget(self.description_edit)

        # Кнопки
        buttons = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)
        
        # Now populate fields if editing after init_ui is built
        if self.payment:
            self.populate_fields()

    def populate_fields(self):
        # Заполняем поля данными из объекта платежа (self.payment)
        if self.payment:
            # Находим индекс договора в комбобоксе
            index = self.contract_combo.findData(self.payment.contract_id)
            if index != -1:
                self.contract_combo.setCurrentIndex(index)

            self.amount_edit.setText(str(self.payment.amount))
            # Используем правильный формат для парсинга даты
            self.payment_date.setDate(QDate.fromString(self.payment.payment_date.strftime("%d.%m.%Y"), "dd.MM.yyyy"))
            self.due_date.setDate(QDate.fromString(self.payment.due_date.strftime("%d.%m.%Y"), "dd.MM.yyyy"))
            # Убедимся, что статус из базы есть в комбобоксе перед установкой
            status_value = self.payment.status.value
            index = self.status_combo.findText(status_value)
            if index != -1:
                self.status_combo.setCurrentIndex(index)

            self.description_edit.setText(self.payment.description)

    def get_payment_data(self):
        """Возвращает данные платежа из полей диалога"""
        try:
            # Удаляем пробелы и заменяем запятую на точку для корректного преобразования во float
            amount_str = self.amount_edit.text().replace(' ', '').replace(',', '.')
            amount = float(amount_str)
            if amount < 0:
                 raise ValueError("Сумма не может быть отрицательной")
        except ValueError as e:
            raise ValueError(f"Некорректная сумма: {e}")

        # Определяем статус на основе даты платежа при создании, или берем из комбобокса при редактировании
        # При редактировании статус берется из комбобокса (который может быть изменен пользователем)
        # При создании статус определяется автоматически по дате оплаты
        status = PaymentStatus(self.status_combo.currentText()) if self.payment else \
                 (PaymentStatus.PAID if self.payment_date.date().toPyDate() <= datetime.now().date() else PaymentStatus.PENDING)

        return {
            'contract_id': self.contract_combo.currentData() if not self.payment else self.payment.contract_id, # Не меняем contract_id при редактировании
            'amount': amount,
            'due_date': self.due_date.date().toPyDate(),
            'payment_date': self.payment_date.date().toPyDate(),
            'status': status,
            'description': self.description_edit.toPlainText()
        }

    def accept(self):
        # Методы accept() и reject() унаследованы от QDialog и используются для закрытия диалога
        super().accept()

    def reject(self):
        super().reject() 