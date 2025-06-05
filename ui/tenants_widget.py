from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                            QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
                            QFormLayout, QLineEdit, QTextEdit, QComboBox)
from PyQt6.QtCore import Qt
from core.database import Tenant, Contract, ContractStatus
from sqlalchemy.orm import Session

class TenantsWidget(QWidget):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.init_ui()

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
            QPushButton:pressed {
                background-color: #0a3d91;
            }
            QLabel {
                color: #ffffff;
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
            }
            QTableWidget::item:selected {
                background-color: #0d47a1; /* Убираем синюю полоску выбора */
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

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Верхняя панель с кнопками
        controls = QHBoxLayout()
        
        # Кнопка добавления
        add_btn = QPushButton("Добавить арендатора")
        add_btn.setMinimumHeight(35)
        add_btn.clicked.connect(self.add_tenant)
        controls.addWidget(add_btn)

        # Кнопка редактирования
        edit_btn = QPushButton("Редактировать")
        edit_btn.setMinimumHeight(35)
        edit_btn.clicked.connect(self.edit_tenant)
        controls.addWidget(edit_btn)

        # Кнопка удаления
        delete_btn = QPushButton("Удалить")
        delete_btn.setMinimumHeight(35)
        delete_btn.clicked.connect(self.delete_tenant)
        controls.addWidget(delete_btn)

        controls.addStretch()
        layout.addLayout(controls)

        # Таблица арендаторов
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
        self.load_tenants()

    def load_tenants(self):
        tenants = self.session.query(Tenant).all()
        
        self.table.setColumnCount(3) # ID, Название, Контактная информация
        self.table.setHorizontalHeaderLabels([
            "ID", "Название", "Контактная информация"
        ])
        self.table.setRowCount(len(tenants))

        for row, tenant in enumerate(tenants):
            self.table.setItem(row, 0, QTableWidgetItem(str(tenant.id)))
            self.table.setItem(row, 1, QTableWidgetItem(tenant.name))
            self.table.setItem(row, 2, QTableWidgetItem(tenant.contact_info))

        self.table.resizeColumnsToContents()

    def add_tenant(self):
        dialog = TenantDialog(self)
        if dialog.exec():
            tenant = Tenant(
                name=dialog.name_edit.text(),
                contact_info=dialog.contact_info_edit.toPlainText() # Используем contact_info
            )
            self.session.add(tenant)
            self.session.commit()
            self.load_tenants()

    def edit_tenant(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            tenant_id = int(self.table.item(current_row, 0).text())
            tenant = self.session.query(Tenant).get(tenant_id)
            if tenant:
                dialog = TenantDialog(self, tenant)
                if dialog.exec():
                    tenant.name = dialog.name_edit.text()
                    tenant.contact_info = dialog.contact_info_edit.toPlainText() # Используем contact_info
                    self.session.commit()
                    self.load_tenants()

    def delete_tenant(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            tenant_id = int(self.table.item(current_row, 0).text())
            tenant = self.session.query(Tenant).get(tenant_id)
            if tenant:
                # Проверяем, есть ли активные договоры
                active_contracts = self.session.query(Contract).filter(
                    Contract.tenant_id == tenant_id,
                    Contract.status == ContractStatus.ACTIVE
                ).count()
                
                if active_contracts > 0:
                    QMessageBox.warning(
                        self,
                        "Ошибка",
                        "Невозможно удалить арендатора с активными договорами"
                    )
                    return

                reply = QMessageBox.question(
                    self,
                    "Подтверждение",
                    "Вы уверены, что хотите удалить этого арендатора?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.session.delete(tenant)
                    self.session.commit()
                    self.load_tenants()

class TenantDialog(QDialog):
    def __init__(self, parent=None, tenant=None):
        super().__init__(parent)
        self.tenant = tenant
        self.init_ui()
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
                /*font-size: 14px;*/ /* Убираем специфический размер шрифта */
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #2b2b2b; /* Изменяем на цвет фона диалога */
                color: #ffffff;
                border: 1px solid #3d3d3d; /* Изменяем на цвет границы как в PaymentDialog */
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #0d47a1;
            }
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 8px 15px; /* Добавляем отступы как в PaymentDialog */
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px; /* Добавляем минимальную ширину */
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0a3d91;
            }
        """)

    def init_ui(self):
        self.setWindowTitle("Арендатор")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Поля ввода
        self.name_edit = QLineEdit()
        self.name_edit.setMinimumHeight(35)
        self.contact_info_edit = QTextEdit()
        self.contact_info_edit.setPlaceholderText("Введите контактное лицо, телефон, email и т.д.")
        self.contact_info_edit.setMinimumHeight(100)

        # Если редактируем существующего арендатора
        if self.tenant:
            self.name_edit.setText(self.tenant.name)
            self.contact_info_edit.setText(self.tenant.contact_info)

        # Добавляем поля в форму
        layout.addRow("Название:", self.name_edit)
        layout.addRow("Контактная информация:", self.contact_info_edit)

        # Кнопки
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        save_btn = QPushButton("Сохранить")
        save_btn.setMinimumHeight(35)
        save_btn.setMinimumWidth(120)
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumHeight(35)
        cancel_btn.setMinimumWidth(120)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow("", buttons)

    def accept(self):
        # Проверяем обязательные поля
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Поле 'Название' обязательно для заполнения")
            return
        
        super().accept() 