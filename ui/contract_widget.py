from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, 
                             QComboBox, QTextEdit, QTableWidget, QTableWidgetItem,
                             QFileDialog, QMessageBox, QDialog, QDateEdit, QFormLayout)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPixmap
from core.database import Contract, Property, Tenant, Payment, ContractStatus, PropertyStatus, PaymentStatus
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os

class ContractWidget(QWidget):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.init_ui()
        self.load_contracts()

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
        """)

        # Apply dark theme stylesheet
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
        """)

        layout = QVBoxLayout(self)

        # Верхняя панель с кнопками
        controls = QHBoxLayout()
        
        # Кнопка добавления
        add_btn = QPushButton("Добавить договор")
        add_btn.setMinimumHeight(35)
        add_btn.clicked.connect(self.show_add_contract_dialog)
        controls.addWidget(add_btn)

        # Кнопка редактирования
        edit_btn = QPushButton("Редактировать")
        edit_btn.setMinimumHeight(35)
        edit_btn.clicked.connect(self.edit_contract)
        controls.addWidget(edit_btn)

        # Кнопка удаления
        delete_btn = QPushButton("Удалить")
        delete_btn.setMinimumHeight(35)
        delete_btn.clicked.connect(self.delete_contract)
        controls.addWidget(delete_btn)

        controls.addStretch()
        layout.addLayout(controls)

        # Таблица договоров
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
            }
            QTableWidget::item:selected {
                #background-color: #0d47a1; /* Убираем синюю полоску выбора */
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
        layout.addWidget(self.table)

        # Загружаем данные
        self.load_contracts()

    def load_contracts(self):
        contracts = self.session.query(Contract).all()

        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Объект", "Арендатор", "Начало", "Окончание", "Аренда в мес.", "Залог", "Статус"
        ])
        self.table.setRowCount(len(contracts))

        for row, contract in enumerate(contracts):
            self.table.setItem(row, 0, QTableWidgetItem(str(contract.id)))
            # Убедимся, что связанные объекты существуют перед доступом к их атрибутам
            property_info = contract.property.address if contract.property else "Объект удален"
            tenant_info = contract.tenant.name if contract.tenant else "Арендатор удален"
            
            self.table.setItem(row, 1, QTableWidgetItem(property_info))
            self.table.setItem(row, 2, QTableWidgetItem(tenant_info))
            self.table.setItem(row, 3, QTableWidgetItem(contract.start_date.strftime("%d.%m.%Y")))
            self.table.setItem(row, 4, QTableWidgetItem(contract.end_date.strftime("%d.%m.%Y")))
            self.table.setItem(row, 5, QTableWidgetItem(f"{contract.rent_amount:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{contract.deposit:.2f}"))
            self.table.setItem(row, 7, QTableWidgetItem(contract.status.value))

        self.table.resizeColumnsToContents()

    def show_add_contract_dialog(self):
        dialog = ContractDialog(self.session)
        if dialog.exec():
            # Получаем данные из диалога
            contract_data = dialog.get_contract_data()

            # Проверяем, что выбраны объект и арендатор
            if contract_data['property_id'] is None or contract_data['tenant_id'] is None:
                QMessageBox.warning(self, "Ошибка", "Необходимо выбрать объект и арендатора")
                return

            # Проверяем, что выбранное имущество доступно
            property = self.session.query(Property).get(contract_data['property_id'])
            if not property or property.status != PropertyStatus.AVAILABLE:
                QMessageBox.warning(self, "Ошибка", "Выбранное имущество недоступно для аренды")
                return

            # Создаем новый договор
            contract = Contract(
                property_id=contract_data['property_id'],
                tenant_id=contract_data['tenant_id'],
                start_date=contract_data['start_date'],
                end_date=contract_data['end_date'],
                rent_amount=contract_data['rent_amount'],
                deposit=contract_data['deposit'],
                area=contract_data['area'], # Добавляем площадь в договор
                status=contract_data['status']
            )
            self.session.add(contract)

            # Обновляем статус имущества на RENTED
            property.status = PropertyStatus.RENTED

            # Создаем первый платеж автоматически
            first_payment_date = contract.start_date
            payment = Payment(
                contract_id=contract.id,
                amount=contract.rent_amount,
                due_date=first_payment_date, # Срок оплаты - дата начала договора
                payment_date=None, # Пока не оплачен
                status=PaymentStatus.PENDING,
                description="Первый ежемесячный платеж"
            )
            self.session.add(payment)

            self.session.commit()
            self.load_contracts()

    def edit_contract(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            contract_id = int(self.table.item(current_row, 0).text())
            contract = self.session.query(Contract).get(contract_id)
            if contract:
                dialog = ContractDialog(self.session, contract)
                if dialog.exec():
                    # Получаем обновленные данные из диалога
                    contract_data = dialog.get_contract_data()

                    # Обновляем поля существующего договора
                    # property_id и tenant_id не должны меняться при редактировании договора через этот диалог
                    contract.start_date = contract_data['start_date']
                    contract.end_date = contract_data['end_date']
                    contract.rent_amount = contract_data['rent_amount']
                    contract.deposit = contract_data['deposit']
                    contract.area = contract_data['area'] # Обновляем площадь
                    contract.status = contract_data['status'] # Статус можно менять при редактировании

                    self.session.commit()
                    self.load_contracts()

    def delete_contract(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            contract_id = int(self.table.item(current_row, 0).text())
            contract = self.session.query(Contract).get(contract_id)
            if contract:
                # Проверяем статус договора перед удалением
                if contract.status == ContractStatus.ACTIVE:
                    reply = QMessageBox.question(
                        self,
                        "Подтверждение",
                        "Этот договор не завершен. Вы уверены, что хотите удалить его?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.No:
                        return
                else:
                     reply = QMessageBox.question(
                         self,
                         "Подтверждение",
                         "Вы уверены, что хотите удалить этот договор?",
                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                     )
                     if reply == QMessageBox.StandardButton.No:
                         return

                # Сохраняем property_id перед удалением договора
                property_id = contract.property_id

                self.session.delete(contract)
                self.session.commit()
                
                # Обновляем статус связанного имущества на AVAILABLE, если оно существует и не связано с другими активными договорами
                if property_id:
                    property = self.session.query(Property).get(property_id)
                    if property:
                        # Проверяем, есть ли другие активные договоры, связанные с этим имуществом
                        other_active_contracts = self.session.query(Contract).filter(
                            Contract.property_id == property_id,
                            Contract.status == ContractStatus.ACTIVE
                        ).count()

                        if other_active_contracts == 0:
                             property.status = PropertyStatus.AVAILABLE
                             self.session.commit()

                self.load_contracts()

class ContractDialog(QDialog):
    def __init__(self, session: Session, contract=None):
        super().__init__()
        self.session = session
        self.contract = contract
        self.init_ui()
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
                border: 1px solid #0d47a1;
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
                image: url(icons/down_arrow.png);
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
            QPushButton:pressed {
                background-color: #0a3d91;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
        """)

    def init_ui(self):
        self.setWindowTitle("Добавить договор" if not self.contract else "Редактировать договор")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Форма ввода данных
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Выбор объекта
        self.property_combo = QComboBox()
        # Для нового договора показываем только доступные объекты
        if not self.contract:
            properties = self.session.query(Property).filter(Property.status == PropertyStatus.AVAILABLE).all()
        else:
            # При редактировании показываем текущий объект и все доступные
            properties = self.session.query(Property).filter(
                (Property.status == PropertyStatus.AVAILABLE) | 
                (Property.id == self.contract.property_id if self.contract else None)
            ).all()

        for property in properties:
            self.property_combo.addItem(property.address, property.id)
        
        # Если редактируем существующий договор, выбираем текущий объект
        if self.contract:
            index = self.property_combo.findData(self.contract.property_id)
            if index != -1:
                self.property_combo.setCurrentIndex(index)
            self.property_combo.setEnabled(False) # Нельзя менять объект у существующего договора

        form_layout.addRow("Объект:", self.property_combo)

        # Выбор арендатора
        self.tenant_combo = QComboBox()
        tenants = self.session.query(Tenant).all()
        for tenant in tenants:
            self.tenant_combo.addItem(tenant.name, tenant.id)
        # Если редактируем существующий договор, выбираем текущего арендатора
        if self.contract:
            index = self.tenant_combo.findData(self.contract.tenant_id)
            if index != -1:
                self.tenant_combo.setCurrentIndex(index)
            self.tenant_combo.setEnabled(False) # Нельзя менять арендатора у существующего договора

        form_layout.addRow("Арендатор:", self.tenant_combo)

        # Даты
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow("Дата начала:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate().addYears(1))
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow("Дата окончания:", self.end_date)

        # Арендная плата
        self.rent_input = QDoubleSpinBox()
        self.rent_input.setRange(0, 1000000)
        self.rent_input.setSuffix(" ₽")
        self.rent_input.setDecimals(2)
        form_layout.addRow("Арендная плата:", self.rent_input)

        # Залог
        self.deposit_input = QDoubleSpinBox()
        self.deposit_input.setRange(0, 1000000)
        self.deposit_input.setSuffix(" ₽")
        self.deposit_input.setDecimals(2)
        form_layout.addRow("Залог:", self.deposit_input)

        # Площадь (для информации, берется из объекта при создании, при редактировании отображается из договора)
        self.area_label = QLabel("Площадь: -")
        form_layout.addRow("Площадь:", self.area_label)

        # Обновляем площадь при выборе объекта (только при создании договора)
        if not self.contract:
            self.property_combo.currentIndexChanged.connect(self.update_area_label)

        # Статус договора (видимо только при редактировании)
        self.status_combo = QComboBox()
        self.status_combo.addItems([status.value for status in ContractStatus])
        if self.contract:
            form_layout.addRow("Статус:", self.status_combo)
            index = self.status_combo.findText(self.contract.status.value)
            if index != -1:
                self.status_combo.setCurrentIndex(index)
        else:
            # При создании договора статус всегда ACTIVE, поле скрыто
            self.status_combo.setVisible(False)

        layout.addLayout(form_layout)

        # Заполняем поля при редактировании
        if self.contract:
            self.populate_fields()

        # Кнопки
        buttons = QHBoxLayout()
        buttons.addStretch()
        save_btn = QPushButton("Сохранить")
        save_btn.setMinimumWidth(100)
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def populate_fields(self):
        # Заполняем поля при редактировании существующего договора
        if self.contract:
            # Находим и устанавливаем выбранный объект и арендатора (комбобоксы отключены)
            property_index = self.property_combo.findData(self.contract.property_id)
            if property_index != -1:
                self.property_combo.setCurrentIndex(property_index)
                # Обновляем площадь для отображения при редактировании
                property = self.session.query(Property).get(self.contract.property_id)
                if property:
                     self.area_label.setText(f"Площадь: {property.area} м²")

            tenant_index = self.tenant_combo.findData(self.contract.tenant_id)
            if tenant_index != -1:
                self.tenant_combo.setCurrentIndex(tenant_index)

            self.start_date.setDate(QDate.fromisoformat(str(self.contract.start_date)))
            self.end_date.setDate(QDate.fromisoformat(str(self.contract.end_date)))
            self.rent_input.setValue(self.contract.rent_amount)
            self.deposit_input.setValue(self.contract.deposit)

    def update_area_label(self, index):
        """Обновляет метку площади при выборе объекта (только при создании)"""
        property_id = self.property_combo.itemData(index)
        if property_id:
            property = self.session.query(Property).get(property_id)
            if property:
                self.area_label.setText(f"Площадь: {property.area} м²")
            else:
                self.area_label.setText("Площадь: -")
        else:
            self.area_label.setText("Площадь: -")

    def get_contract_data(self):
        """Возвращает данные договора из полей диалога"""
        return {
            'property_id': self.property_combo.currentData(),
            'tenant_id': self.tenant_combo.currentData(),
            'start_date': self.start_date.date().toPyDate(),
            'end_date': self.end_date.date().toPyDate(),
            'rent_amount': self.rent_input.value(),
            'deposit': self.deposit_input.value(),
            'area': self.session.query(Property).get(self.property_combo.currentData()).area if self.property_combo.currentData() else 0.0, # Берем площадь из выбранного объекта
            'status': ContractStatus(self.status_combo.currentText()) if self.contract else ContractStatus.ACTIVE # Статус берется из комбобокса при редактировании, ACTIVE при создании
        }

    # Методы accept() и reject() унаследованы от QDialog и используются для закрытия диалога 