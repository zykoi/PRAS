from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                            QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
                            QFormLayout, QLineEdit, QTextEdit, QComboBox, QDateEdit,
                            QFileDialog)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from core.database import Contract, Property, Payment, Tenant
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class AnalyticsWidget(QWidget):
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
            /* Добавьте остальные стили по необходимости */
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Верхняя панель с элементами управления
        controls = QHBoxLayout()
        controls.setSpacing(10)
        
        # Выбор типа аналитики
        self.analytics_type = QComboBox()
        self.analytics_type.setMinimumWidth(200)
        self.analytics_type.setMinimumHeight(35)
        self.analytics_type.addItems([
            "Доходы по месяцам",
            "Загруженность помещений",
            "Топ арендаторов",
            "Динамика платежей"
        ])
        self.analytics_type.currentTextChanged.connect(self.update_analytics)
        controls.addWidget(QLabel("Тип аналитики:"))
        controls.addWidget(self.analytics_type)

        # Период анализа
        self.start_date = QDateEdit()
        self.start_date.setMinimumHeight(35)
        self.start_date.setDate(QDate.currentDate().addMonths(-12))
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

        # Область для графика
        self.figure = Figure(figsize=(8, 6), facecolor='#2b2b2b')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: none;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.canvas)

        # Таблица с данными
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
                background-color: #0d47a1;
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
        self.update_analytics()

    def update_analytics(self):
        analytics_type = self.analytics_type.currentText()
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()

        if analytics_type == "Доходы по месяцам":
            self.show_monthly_income(start_date, end_date)
        elif analytics_type == "Загруженность помещений":
            self.show_occupancy_analytics()
        elif analytics_type == "Топ арендаторов":
            self.show_top_tenants(start_date, end_date)
        elif analytics_type == "Динамика платежей":
            self.show_payment_dynamics(start_date, end_date)

    def show_monthly_income(self, start_date, end_date):
        # Получаем данные
        payments = self.session.query(
            func.strftime('%Y-%m', Payment.payment_date).label('month'),
            func.sum(Payment.amount).label('total_amount')
        ).filter(
            Payment.payment_date.between(start_date, end_date),
            Payment.status == 'paid'
        ).group_by('month').all()

        # Очищаем график
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Строим график
        months = [datetime.strptime(p.month, '%Y-%m').strftime("%B %Y") for p in payments]
        amounts = [p.total_amount for p in payments]
        ax.bar(months, amounts)
        ax.set_title("Доходы по месяцам")
        ax.set_xlabel("Месяц")
        ax.set_ylabel("Сумма (₽)")
        plt.xticks(rotation=45)
        self.figure.tight_layout()
        self.canvas.draw()

        # Обновляем таблицу
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Месяц", "Сумма"])
        self.table.setRowCount(len(payments))
        for i, payment in enumerate(payments):
            month_date = datetime.strptime(payment.month, '%Y-%m')
            self.table.setItem(i, 0, QTableWidgetItem(month_date.strftime("%B %Y")))
            self.table.setItem(i, 1, QTableWidgetItem(f"{payment.total_amount:.2f} ₽"))
        self.table.resizeColumnsToContents()

    def show_occupancy_analytics(self):
        # Получаем данные
        properties = self.session.query(Property).all()
        
        # Очищаем график
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Строим график
        names = [p.name for p in properties]
        areas = [p.area for p in properties]
        rented_areas = [sum(c.area for c in p.contracts if c.status == 'active') for p in properties]
        
        x = range(len(names))
        width = 0.35
        
        ax.bar(x, areas, width, label='Общая площадь')
        ax.bar([i + width for i in x], rented_areas, width, label='Арендованная площадь')
        
        ax.set_title("Загруженность помещений")
        ax.set_xlabel("Объект")
        ax.set_ylabel("Площадь (м²)")
        ax.set_xticks([i + width/2 for i in x])
        ax.set_xticklabels(names, rotation=45)
        ax.legend()
        
        self.figure.tight_layout()
        self.canvas.draw()

        # Обновляем таблицу
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Объект", "Общая площадь", "Арендованная площадь", "Загруженность"
        ])
        self.table.setRowCount(len(properties))
        for i, property in enumerate(properties):
            rented_area = sum(c.area for c in property.contracts if c.status == 'active')
            occupancy = (rented_area / property.area * 100) if property.area > 0 else 0
            
            self.table.setItem(i, 0, QTableWidgetItem(property.name))
            self.table.setItem(i, 1, QTableWidgetItem(f"{property.area:.2f} м²"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{rented_area:.2f} м²"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{occupancy:.1f}%"))
        self.table.resizeColumnsToContents()

    def show_top_tenants(self, start_date, end_date):
        # Получаем данные
        tenants = self.session.query(Tenant, func.sum(Payment.amount)).select_from(Tenant).join(Contract).join(Payment).group_by(Tenant.id).order_by(func.sum(Payment.amount).desc()).all()

        # Очищаем график
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Строим график
        names = [t[0].name for t in tenants]
        amounts = [t[1] for t in tenants]
        ax.bar(names, amounts)
        ax.set_title("Топ арендаторов по платежам")
        ax.set_xlabel("Арендатор")
        ax.set_ylabel("Сумма платежей (₽)")
        plt.xticks(rotation=45)
        self.figure.tight_layout()
        self.canvas.draw()

        # Обновляем таблицу
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Арендатор", "Сумма платежей"])
        self.table.setRowCount(len(tenants))
        for i, (tenant, amount) in enumerate(tenants):
            self.table.setItem(i, 0, QTableWidgetItem(tenant.name))
            self.table.setItem(i, 1, QTableWidgetItem(f"{amount:.2f} ₽"))
        self.table.resizeColumnsToContents()

    def show_payment_dynamics(self, start_date, end_date):
        # Получаем данные
        payments = self.session.query(
            func.strftime('%Y-%m', Payment.due_date).label('month'),
            func.count(Payment.id).label('total_payments'),
            func.sum(case((Payment.status == 'paid', Payment.amount), else_=0)).label('paid_amount'),
            func.sum(case((Payment.status == 'overdue', Payment.amount), else_=0)).label('overdue_amount')
        ).filter(
            Payment.due_date.between(start_date, end_date)
        ).group_by('month').all()

        # Очищаем график
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Строим график
        months = [p.month for p in payments]
        paid = [p.paid_amount for p in payments]
        overdue = [p.overdue_amount for p in payments]
        
        x = range(len(months))
        width = 0.35
        
        ax.bar(x, paid, width, label='Оплачено')
        ax.bar([i + width for i in x], overdue, width, label='Просрочено')
        
        ax.set_title("Динамика платежей")
        ax.set_xlabel("Месяц")
        ax.set_ylabel("Сумма (₽)")
        ax.set_xticks([i + width/2 for i in x])
        ax.set_xticklabels(months, rotation=45)
        ax.legend()
        
        self.figure.tight_layout()
        self.canvas.draw()

        # Обновляем таблицу
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Месяц", "Количество платежей", "Оплачено", "Просрочено"
        ])
        self.table.setRowCount(len(payments))
        for i, payment in enumerate(payments):
            self.table.setItem(i, 0, QTableWidgetItem(payment.month))
            self.table.setItem(i, 1, QTableWidgetItem(str(payment.total_payments)))
            self.table.setItem(i, 2, QTableWidgetItem(f"{payment.paid_amount:.2f} ₽"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{payment.overdue_amount:.2f} ₽"))
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