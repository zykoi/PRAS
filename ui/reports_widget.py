from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                            QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
                            QFormLayout, QLineEdit, QTextEdit, QComboBox, QDateEdit, QGroupBox, QScrollArea)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from core.database import Contract, Property, Payment
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import pandas as pd
import os

class ReportsWidget(QWidget):
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
            QPushButton:pressed {
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

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Верхняя панель с элементами управления
        controls = QHBoxLayout()
        controls.setSpacing(10)
        
        # Выбор типа отчета
        self.report_type = QComboBox()
        self.report_type.setMinimumWidth(200)
        self.report_type.setMinimumHeight(35)
        self.report_type.addItems([
            "Арендные платежи по объектам",
            "Просроченные платежи",
            "Загруженность помещений",
            "Финансовый отчет"
        ])
        self.report_type.currentTextChanged.connect(self.update_report)
        controls.addWidget(QLabel("Тип отчета:"))
        controls.addWidget(self.report_type)

        # Период отчета
        self.start_date = QDateEdit()
        self.start_date.setMinimumHeight(35)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date = QDateEdit()
        self.end_date.setMinimumHeight(35)
        self.end_date.setDate(QDate.currentDate())
        controls.addWidget(QLabel("С:"))
        controls.addWidget(self.start_date)
        controls.addWidget(QLabel("По:"))
        controls.addWidget(self.end_date)

        # Кнопка экспорта
        export_btn = QPushButton("Экспорт в Excel")
        export_btn.setMinimumHeight(35)
        export_btn.setMinimumWidth(150)
        export_btn.clicked.connect(self.export_to_excel)
        controls.addWidget(export_btn)

        controls.addStretch()
        layout.addLayout(controls)

        # Таблица для отображения отчета
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

        # Инициализация первого отчета
        self.update_report()

    def update_report(self):
        report_type = self.report_type.currentText()
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()

        if report_type == "Арендные платежи по объектам":
            self.show_rental_payments_report(start_date, end_date)
        elif report_type == "Просроченные платежи":
            self.show_overdue_payments_report()
        elif report_type == "Загруженность помещений":
            self.show_occupancy_report()
        elif report_type == "Финансовый отчет":
            self.show_financial_report(start_date, end_date)

    def show_rental_payments_report(self, start_date, end_date):
        payments = self.session.query(
            Property.name.label('property_name'),
            func.sum(Payment.amount).label('total_amount')
        ).select_from(Property)
        payments = payments.join(Contract, Contract.property_id == Property.id)
        payments = payments.join(Payment, Payment.contract_id == Contract.id)
        payments = payments.filter(
            Payment.payment_date.between(start_date, end_date)
        ).group_by(Property.name).all()

        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Объект", "Сумма платежей"])
        self.table.setRowCount(len(payments))

        for row, (property_name, total_amount) in enumerate(payments):
            self.table.setItem(row, 0, QTableWidgetItem(property_name))
            self.table.setItem(row, 1, QTableWidgetItem(f"{total_amount:.2f} ₽"))

        self.table.resizeColumnsToContents()

    def show_overdue_payments_report(self):
        overdue_payments = self.session.query(Payment).filter(
            Payment.status == 'overdue'
        ).all()

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Договор", "Сумма", "Срок оплаты", "Дней просрочки"
        ])
        self.table.setRowCount(len(overdue_payments))

        for row, payment in enumerate(overdue_payments):
            days_overdue = (datetime.now().date() - payment.due_date).days
            self.table.setItem(row, 0, QTableWidgetItem(f"Договор №{payment.contract.id}"))
            self.table.setItem(row, 1, QTableWidgetItem(f"{payment.amount:.2f} ₽"))
            self.table.setItem(row, 2, QTableWidgetItem(payment.due_date.strftime("%d.%m.%Y")))
            self.table.setItem(row, 3, QTableWidgetItem(str(days_overdue)))

        self.table.resizeColumnsToContents()

    def show_occupancy_report(self):
        properties = self.session.query(Property).all()
        
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Объект", "Общая площадь", "Арендованная площадь", "Загруженность"
        ])
        self.table.setRowCount(len(properties))

        for row, property in enumerate(properties):
            rented_area = sum(contract.area for contract in property.contracts)
            occupancy = (rented_area / property.area * 100) if property.area > 0 else 0
            
            self.table.setItem(row, 0, QTableWidgetItem(property.name))
            self.table.setItem(row, 1, QTableWidgetItem(f"{property.area:.2f} м²"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{rented_area:.2f} м²"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{occupancy:.1f}%"))

        self.table.resizeColumnsToContents()

    def show_financial_report(self, start_date, end_date):
        payments = self.session.query(
            func.strftime('%Y-%m', Payment.payment_date).label('month'),
            func.sum(Payment.amount).label('total_amount')
        ).filter(
            Payment.payment_date.between(start_date, end_date)
        ).group_by('month').all()

        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Месяц", "Сумма платежей"])
        self.table.setRowCount(len(payments))

        for row, (month, total_amount) in enumerate(payments):
            self.table.setItem(row, 0, QTableWidgetItem(month))
            self.table.setItem(row, 1, QTableWidgetItem(f"{total_amount:.2f} ₽"))

        self.table.resizeColumnsToContents()

    def export_to_excel(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчет",
            "",
            "Excel Files (*.xlsx)"
        )
        
        if file_name:
            # Создаем DataFrame из данных таблицы
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            df = pd.DataFrame(data, columns=[self.table.horizontalHeaderItem(i).text() 
                                           for i in range(self.table.columnCount())])
            
            # Сохраняем в Excel
            df.to_excel(file_name, index=False)
            QMessageBox.information(self, "Успех", "Отчет успешно экспортирован в Excel") 