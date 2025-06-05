from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, 
                             QComboBox, QTextEdit, QTableWidget, QTableWidgetItem,
                             QFileDialog, QMessageBox, QDialog, QScrollArea, QGridLayout, QGroupBox, QFormLayout, QFrame, QSpacerItem, QDialogButtonBox, QListWidget)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QImage, QColor
from core.database import Property, PropertyPhoto, InventoryItem, PropertyStatus, Contract
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime

class PhotoDialog(QDialog):
    def __init__(self, property_id, session):
        super().__init__()
        self.property_id = property_id
        self.session = session
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Фотографии помещения")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)

        # Область просмотра фотографий
        scroll = QScrollArea()
        self.photos_widget = QWidget()
        self.photos_layout = QGridLayout(self.photos_widget)
        self.photos_layout.setContentsMargins(0, 0, 0, 0)
        self.photos_layout.setSpacing(10) # Отступ между фотографиями
        scroll.setWidget(self.photos_widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)
        layout.addWidget(scroll)

        # Кнопки управления
        buttons = QHBoxLayout()
        buttons.addStretch()
        add_btn = QPushButton("Добавить фото")
        add_btn.clicked.connect(self.add_photo)
        buttons.addWidget(add_btn)
        layout.addLayout(buttons)

        self.load_photos()

    def load_photos(self):
        # Очищаем текущие фотографии
        for i in reversed(range(self.photos_layout.count())): 
            self.photos_layout.itemAt(i).widget().setParent(None)

        # Загружаем фотографии из базы
        self.photos = self.session.query(PropertyPhoto).filter(
            PropertyPhoto.property_id == self.property_id
        ).all()

        row = 0
        col = 0
        for i, photo in enumerate(self.photos):
            if os.path.exists(photo.file_path):
                # Создаем виджет для фотографии
                photo_widget = QWidget()
                photo_layout = QVBoxLayout(photo_widget)
                photo_layout.setContentsMargins(0, 0, 0, 0)

                # Отображаем фотографию
                label = QLabel()
                pixmap = QPixmap(photo.file_path)
                label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
                label.setCursor(Qt.CursorShape.PointingHandCursor)
                label.setStyleSheet("""
                    QLabel {
                        border: 1px solid #3d3d3d;
                        border-radius: 5px;
                        padding: 5px;
                        background-color: #1e1e1e;
                    }
                    QLabel:hover {
                        border: 1px solid #0d47a1;
                    }
                """)
                label.mousePressEvent = lambda event, path=photo.file_path, index=i: self.show_full_photo(path, index)
                photo_layout.addWidget(label)

                # Добавляем описание
                desc_label = QLabel(photo.description)
                desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                desc_label.setStyleSheet("color: #bbbbbb;")
                photo_layout.addWidget(desc_label)

                # Добавляем кнопки управления
                buttons = QHBoxLayout()
                buttons.addStretch()
                delete_btn = QPushButton("Удалить")
                delete_btn.clicked.connect(lambda checked, p=photo: self.delete_photo(p))
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #d32f2f;
                        color: white;
                        border: none;
                        padding: 3px 8px;
                        border-radius: 3px;
                        font-weight: normal;
                        font-size: 10px;
                    }
                    QPushButton:hover {
                        background-color: #e53935;
                    }
                """)
                buttons.addWidget(delete_btn)
                photo_layout.addLayout(buttons)

                self.photos_layout.addWidget(photo_widget, row, col)
                col += 1
                if col > 3:  # 4 фотографии в ряд
                    col = 0
                    row += 1

    def add_photo(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите фотографию",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        if file_name:
            # Для PhotoDialog, мы сразу сохраняем фото в папку property_id
            # (Этот диалог вызывается только для существующих объектов)
            photos_dir = f"photos/property_{self.property_id}"
            os.makedirs(photos_dir, exist_ok=True)

            # Копируем файл
            new_file_name = f"{photos_dir}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_name)}"
            shutil.copy2(file_name, new_file_name)

            # Добавляем запись в базу
            photo = PropertyPhoto(
                property_id=self.property_id,
                file_path=new_file_name,
                description="",
                is_main=0 # По умолчанию не главная
            )
            self.session.add(photo)
            self.session.commit()

            self.load_photos()

    def set_main_photo(self, photo):
        # Сбрасываем флаг главной фотографии у всех фотографий для данного объекта
        self.session.query(PropertyPhoto).filter(
            PropertyPhoto.property_id == self.property_id
        ).update({"is_main": 0})

        # Устанавливаем новую главную фотографию
        photo.is_main = 1
        self.session.commit()
        self.load_photos()

    def delete_photo(self, photo):
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить фотографию?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Удаляем файл
            if os.path.exists(photo.file_path):
                os.remove(photo.file_path)
            
            # Удаляем запись из базы
            self.session.delete(photo)
            self.session.commit()
            self.load_photos()

    def show_full_photo(self, photo_path, current_index):
        """Открывает фотографию во весь экран с возможностью листания"""
        photo_paths = [p.file_path for p in self.photos if os.path.exists(p.file_path)]
        if not photo_paths:
            return
        dialog = PhotoViewerDialog(photo_paths, current_index, self)
        dialog.exec()

class InventoryDialog(QDialog):
    def __init__(self, property_id, session):
        super().__init__()
        self.property_id = property_id
        self.session = session
        self.init_ui()
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
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
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #3d3d3d;
                border: none;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0d47a1;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                color: #ffffff;
                padding: 5px;
                border: none;
                border-right: 1px solid #3d3d3d;
                border-bottom: 1px solid #3d3d3d;
            }
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0a3d91;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #0d47a1;
            }
        """)

    def init_ui(self):
        self.setWindowTitle("Инвентаризация помещения")
        self.setMinimumSize(800, 600)  # Увеличиваем размер окна
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Таблица инвентаря
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Наименование", "Описание", "Количество", "Состояние", "Примечания", ""
        ])
        # Устанавливаем ширину столбцов
        self.table.setColumnWidth(0, 150)  # Наименование
        self.table.setColumnWidth(1, 200)  # Описание
        self.table.setColumnWidth(2, 100)  # Количество
        self.table.setColumnWidth(3, 100)  # Состояние
        self.table.setColumnWidth(4, 200)  # Примечания
        self.table.setColumnWidth(5, 100)  # Кнопка удаления
        layout.addWidget(self.table)

        # Кнопки управления
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        
        add_btn = QPushButton("Добавить предмет")
        add_btn.setMinimumWidth(150)
        add_btn.clicked.connect(self.add_item)
        buttons.addWidget(add_btn)
        
        buttons.addStretch()
        layout.addLayout(buttons)

        self.load_inventory()

    def load_inventory(self):
        if not self.property_id:
            return

        items = self.session.query(InventoryItem).filter(
            InventoryItem.property_id == self.property_id
        ).all()

        self.table.setRowCount(len(items))
        for i, item in enumerate(items):
            self.table.setItem(i, 0, QTableWidgetItem(item.name))
            self.table.setItem(i, 1, QTableWidgetItem(item.description))
            self.table.setItem(i, 2, QTableWidgetItem(str(item.quantity)))
            self.table.setItem(i, 3, QTableWidgetItem(item.condition))
            self.table.setItem(i, 4, QTableWidgetItem(item.notes))

            # Кнопка удаления
            delete_btn = QPushButton("Удалить")
            delete_btn.clicked.connect(lambda checked, row=i: self.delete_item(row))
            self.table.setCellWidget(i, 5, delete_btn)

    def add_item(self):
        dialog = InventoryItemDialog(self)
        if dialog.exec():
            if not self.property_id:
                QMessageBox.warning(self, "Ошибка", "Сначала сохраните объект")
                return

            item = InventoryItem(
                property_id=self.property_id,
                name=dialog.name_edit.text(),
                description=dialog.description_edit.toPlainText(),
                quantity=int(dialog.quantity_spin.value()),
                condition=dialog.condition_combo.currentText(),
                notes=dialog.notes_edit.toPlainText()
            )
            self.session.add(item)
            self.session.commit()
            self.load_inventory()

    def delete_item(self, row):
        if not self.property_id:
            return

        item_name = self.table.item(row, 0).text()
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить предмет '{item_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            item = self.session.query(InventoryItem).filter(
                InventoryItem.property_id == self.property_id,
                InventoryItem.name == item_name
            ).first()
            if item:
                self.session.delete(item)
                self.session.commit()
                self.load_inventory()

class InventoryItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
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
            QPushButton:pressed {
                background-color: #0a3d91;
            }
        """)

    def init_ui(self):
        self.setWindowTitle("Добавить предмет")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Наименование
        name_layout = QHBoxLayout()
        name_label = QLabel("Наименование:")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите наименование предмета")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Описание
        desc_label = QLabel("Описание:")
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Введите описание предмета")
        self.description_edit.setMaximumHeight(100)
        layout.addWidget(desc_label)
        layout.addWidget(self.description_edit)

        # Количество
        quantity_layout = QHBoxLayout()
        quantity_label = QLabel("Количество:")
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(9999)
        quantity_layout.addWidget(quantity_label)
        quantity_layout.addWidget(self.quantity_spin)
        layout.addLayout(quantity_layout)

        # Состояние
        condition_layout = QHBoxLayout()
        condition_label = QLabel("Состояние:")
        self.condition_combo = QComboBox()
        self.condition_combo.addItems(["Новое", "Хорошее", "Среднее", "Плохое"])
        condition_layout.addWidget(condition_label)
        condition_layout.addWidget(self.condition_combo)
        layout.addLayout(condition_layout)

        # Примечания
        notes_label = QLabel("Примечания:")
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Введите примечания")
        self.notes_edit.setMaximumHeight(100)
        layout.addWidget(notes_label)
        layout.addWidget(self.notes_edit)

        # Кнопки
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addStretch()
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

class PhotoViewerDialog(QDialog):
    def __init__(self, photo_paths, current_index, parent=None):
        super().__init__(parent)
        self.photo_paths = photo_paths
        self.current_index = current_index
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Просмотр фотографии")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        
        layout = QVBoxLayout(self)
        
        # Создаем скролл-область для фотографии
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        # Создаем метку для фотографии
        photo_label = QLabel()
        pixmap = QPixmap(self.photo_paths[self.current_index])
        photo_label.setPixmap(pixmap)
        photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label = photo_label # Сохраняем ссылку на метку фото
        
        scroll.setWidget(photo_label)
        layout.addWidget(scroll)
        
        # Кнопки навигации и закрытия
        controls_layout = QHBoxLayout()
        controls_layout.addStretch()

        self.prev_btn = QPushButton("Назад")
        self.prev_btn.clicked.connect(self.show_previous_photo)
        controls_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Вперед")
        self.next_btn.clicked.connect(self.show_next_photo)
        controls_layout.addWidget(self.next_btn)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        controls_layout.addWidget(close_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        self.update_buttons_state()

    def update_photo(self):
        """Обновляет отображаемую фотографию"""
        if 0 <= self.current_index < len(self.photo_paths):
            pixmap = QPixmap(self.photo_paths[self.current_index])
            self.photo_label.setPixmap(pixmap)
            self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_buttons_state()

    def update_buttons_state(self):
        """Обновляет состояние кнопок навигации"""
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.photo_paths) - 1)

    def show_previous_photo(self):
        """Показывает предыдущую фотографию"""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_photo()

    def show_next_photo(self):
        """Показывает следующую фотографию"""     
        if self.current_index < len(self.photo_paths) - 1:
            self.current_index += 1
            self.update_photo()

class PropertyDialog(QDialog):
    def __init__(self, parent=None, property=None):
        super().__init__(parent)
        self.property = property
        self.temp_photos = []  # Список для хранения временных фотографий
        self.init_ui()
        if property:
            self.populate_fields()

    def init_ui(self):
        self.setWindowTitle("Добавить имущество" if not self.property else "Редактировать имущество")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        # Форма ввода данных
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Наименование
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите наименование имущества")
        form_layout.addRow("Наименование:", self.name_edit)

        # Адрес
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Введите адрес")
        form_layout.addRow("Адрес:", self.address_edit)

        # Площадь
        self.area_edit = QDoubleSpinBox()
        self.area_edit.setRange(0, 10000)
        self.area_edit.setSuffix(" м²")
        self.area_edit.setDecimals(2)
        form_layout.addRow("Площадь:", self.area_edit)

        # Этаж
        self.floor_edit = QSpinBox()
        self.floor_edit.setRange(-10, 200)
        self.floor_edit.setSuffix(" этаж")
        form_layout.addRow("Этаж:", self.floor_edit)

        # Статус
        self.status_combo = QComboBox()
        self.status_combo.addItems([status.value for status in PropertyStatus])
        form_layout.addRow("Статус:", self.status_combo)

        # Описание
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Введите описание имущества")
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Описание:", self.description_edit)

        layout.addLayout(form_layout)

        # Раздел для фотографий
        photos_group = QGroupBox("Фотографии")
        photos_layout = QVBoxLayout(photos_group)
        
        self.photos_area = QScrollArea()
        self.photos_area.setWidgetResizable(True)
        self.photos_widget = QWidget()
        self.photos_grid_layout = QGridLayout(self.photos_widget)
        self.photos_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.photos_grid_layout.setSpacing(10) # Отступ между фотографиями
        self.photos_area.setWidget(self.photos_widget)
        self.photos_area.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)
        photos_layout.addWidget(self.photos_area)
        
        add_photo_btn = QPushButton("Добавить фото")
        add_photo_btn.clicked.connect(self.add_photo)
        photos_layout.addWidget(add_photo_btn)
        
        layout.addWidget(photos_group)

        # Раздел для инвентаризации (только при редактировании)
        if self.property:
            inventory_group = QGroupBox("Инвентаризация")
            inventory_layout = QVBoxLayout(inventory_group)

            inventory_btn = QPushButton("Управление инвентарем")
            inventory_btn.clicked.connect(self.show_inventory)
            inventory_layout.addWidget(inventory_btn)

            layout.addWidget(inventory_group)

            # Кнопка истории аренды (только при редактировании)
            self.rental_history_button = QPushButton("История аренды")
            self.rental_history_button.clicked.connect(self.show_rental_history)
            layout.addWidget(self.rental_history_button)

        # Кнопки
        buttons = QHBoxLayout()
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
        if self.property:
            self.name_edit.setText(self.property.name)
            self.address_edit.setText(self.property.address)
            self.area_edit.setValue(self.property.area)
            self.floor_edit.setValue(self.property.floor)
            self.status_combo.setCurrentText(self.property.status.value)
            self.description_edit.setText(self.property.description)
            self.load_photos() # Загружаем фотографии при редактировании

    def get_property_data(self):
        return {
            'name': self.name_edit.text(),
            'address': self.address_edit.text(),
            'area': self.area_edit.value(),
            'floor': self.floor_edit.value(),
            'status': PropertyStatus(self.status_combo.currentText()),
            'description': self.description_edit.toPlainText()
        }

    def add_photo(self):
        """Добавление фотографии к объекту недвижимости"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите фотографию",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        if file_name:
            # Создаем временную копию файла
            temp_dir = "temp_photos"
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = f"{temp_dir}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_name)}"
            shutil.copy2(file_name, temp_file)
            
            # Добавляем во временный список
            self.temp_photos.append(temp_file)
            
            # Обновляем отображение
            self.load_photos()

    def load_photos(self):
        # Очищаем текущие фотографии
        while self.photos_grid_layout.count():
            item = self.photos_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Загружаем фотографии из базы для существующего объекта
        self.db_photos = [] # Храним фотографии из базы отдельно
        if self.property and self.property.id:
            self.db_photos = self.parent().session.query(PropertyPhoto).filter(
                PropertyPhoto.property_id == self.property.id
            ).all()
            
        all_photos_paths = [p.file_path for p in self.db_photos if os.path.exists(p.file_path)] + \
                           [p for p in self.temp_photos if os.path.exists(p)]

        # Добавляем все фотографии в сетку
        row = 0
        col = 0
        photos_per_row = 3 # Количество фотографий в одном ряду

        for i, photo_path in enumerate(all_photos_paths):
            self.add_photo_to_grid(photo_path, row, col)
            col += 1
            if col >= photos_per_row:
                col = 0
                row += 1

    def add_photo_to_grid(self, photo_path, row, col):
        """Добавляет фотографию в сетку с кнопкой удаления по заданным координатам"""
        
        photo_widget = QWidget()
        photo_layout = QVBoxLayout(photo_widget)
        photo_layout.setContentsMargins(0, 0, 0, 0)
        
        photo_label = QLabel()
        pixmap = QPixmap(photo_path)
        photo_label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
        photo_label.setCursor(Qt.CursorShape.PointingHandCursor)
        photo_label.setStyleSheet("""
            QLabel {
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 5px;
                background-color: #1e1e1e;
            }
            QLabel:hover {
                border: 1px solid #0d47a1;
            }
        """)
        
        # Добавляем обработчик клика для открытия фото во весь экран
        photo_label.mousePressEvent = lambda event, path=photo_path: self.show_full_photo(path)
        
        photo_layout.addWidget(photo_label)

        # Кнопка удаления
        delete_btn = QPushButton("Удалить")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                padding: 3px 8px;
                border-radius: 3px;
                font-weight: normal;
                font-size: 10px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
        """)
        # Связываем кнопку удаления с методом delete_photo_by_path
        delete_btn.clicked.connect(lambda checked, path=photo_path: self.delete_photo_by_path(path))
        
        photo_layout.addWidget(delete_btn)
        
        self.photos_grid_layout.addWidget(photo_widget, row, col)

    def delete_photo_by_path(self, photo_path):
        """Удаляет фотографию по пути файла"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить фотографию?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Проверяем, является ли фото временным или из базы
            if photo_path in self.temp_photos:
                # Удаляем из временного списка и файла
                self.temp_photos.remove(photo_path)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            elif self.property and self.property.id:
                # Удаляем из базы и файла
                photo = self.parent().session.query(PropertyPhoto).filter(
                    PropertyPhoto.property_id == self.property.id,
                    PropertyPhoto.file_path == photo_path
                ).first()
                if photo:
                    self.parent().session.delete(photo)
                    self.parent().session.commit()
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
            
            # Обновляем отображение
            self.load_photos()

    def show_full_photo(self, photo_path):
        """Открывает фотографию во весь экран"""
        # Собираем список всех фотографий (из базы и временные)
        all_photo_paths = []
        if self.property and self.property.id:
            db_photos = self.parent().session.query(PropertyPhoto).filter(
                PropertyPhoto.property_id == self.property.id
            ).all()
            all_photo_paths.extend([p.file_path for p in db_photos if os.path.exists(p.file_path)])

        all_photo_paths.extend([p for p in self.temp_photos if os.path.exists(p)])

        if not all_photo_paths:
            return

        # Находим индекс текущей фотографии
        try:
            current_index = all_photo_paths.index(photo_path)
        except ValueError:
            current_index = 0 # Если фото не найдено, показываем первое

        # Открываем диалог просмотра
        dialog = PhotoViewerDialog(all_photo_paths, current_index, self)
        dialog.exec()

    def accept(self):
        # Проверяем заполнение обязательных полей
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите наименование имущества")
            self.name_edit.setFocus()
            return
            
        if not self.address_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите адрес")
            self.address_edit.setFocus()
            return
            
        if self.area_edit.value() <= 0:
            QMessageBox.warning(self, "Ошибка", "Площадь должна быть больше 0")
            self.area_edit.setFocus()
            return

        # Сохраняем объект только если это редактирование
        if self.property:
            property_data = self.get_property_data()
            for key, value in property_data.items():
                setattr(self.property, key, value)
            self.parent().session.commit()

            # Перемещаем временные фотографии в постоянную папку
            if self.temp_photos:
                photos_dir = f"photos/property_{self.property.id}"
                os.makedirs(photos_dir, exist_ok=True)
                
                for temp_photo in self.temp_photos:
                    new_file_name = f"{photos_dir}/{os.path.basename(temp_photo)}"
                    shutil.move(temp_photo, new_file_name)
                    
                    # Добавляем запись в базу
                    photo = PropertyPhoto(
                        property_id=self.property.id,
                        file_path=new_file_name,
                        description="",
                        is_main=0
                    )
                    self.parent().session.add(photo)
                
                self.parent().session.commit()
            
        super().accept()

    def reject(self):
        # Удаляем временные фотографии при отмене
        for temp_photo in self.temp_photos:
            if os.path.exists(temp_photo):
                os.remove(temp_photo)
        super().reject()

    def show_inventory(self):
        """Открывает диалог инвентаризации для текущего объекта"""
        dialog = InventoryDialog(self.property.id if self.property else None, self.parent().session)
        dialog.exec()

    def show_rental_history(self):
        """Открывает диалог истории аренды для текущего объекта"""
        if self.property and self.property.id:
            dialog = RentalHistoryDialog(self.parent().session, self.property.id)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Ошибка", "Невозможно отобразить историю аренды для несохраненного объекта.")

class RentalHistoryDialog(QDialog):
    def __init__(self, session: Session, property_id: int):
        super().__init__()
        self.session = session
        self.property_id = property_id
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("История аренды объекта")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        # Применяем стили темной темы
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QListWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3d3d3d;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
        """)

        self.history_list = QListWidget()
        layout.addWidget(self.history_list)

        self.load_rental_history()

    def load_rental_history(self):
        self.history_list.clear()
        contracts = self.session.query(Contract).filter(Contract.property_id == self.property_id).all()

        if not contracts:
            self.history_list.addItem("Нет данных об аренде для этого объекта.")
            return

        for contract in contracts:
            # Явно обновляем атрибуты объекта из базы данных
            self.session.refresh(contract)
            item_text = f"Договор №{contract.id} от {contract.start_date.strftime('%Y-%m-%d')} " \
                        f"до {contract.end_date.strftime('%Y-%m-%d')}\n" \
                        f"Арендатор: {contract.tenant.name}\n" \
                        f"Стоимость: {contract.rent_amount:.2f} ₽/мес"
            
            # Проверяем статус договора и добавляем индикатор
            if contract.status == 'active':
                item_text += "\nСтатус: Активный"
            elif contract.status == 'completed':
                 item_text += "\nСтатус: Завершен"
            self.history_list.addItem(item_text)

class PropertyWidget(QWidget):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.selected_card = None  # Добавляем переменную для хранения выбранной карточки
        self.selected_property = None  # Добавляем переменную для хранения выбранного объекта
        self.init_ui()
        self.load_properties()

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
             QScrollArea {
                 border: none;
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
        """)

        layout = QVBoxLayout(self)

        # Верхняя панель с элементами управления
        controls = QHBoxLayout()
        
        # Кнопки
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_property)
        controls.addWidget(add_btn)

        controls.addStretch()
        layout.addLayout(controls)

        # Создаем скролл-область для списка имущества
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Контейнер для списка имущества
        self.properties_container = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_container)
        self.properties_layout.setSpacing(20)
        scroll.setWidget(self.properties_container)
        
        layout.addWidget(scroll)

    def load_properties(self):
        # Очищаем текущий layout
        while self.properties_layout.count():
            item = self.properties_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Рекурсивно удаляем все виджеты из вложенного layout
                while item.layout().count():
                    nested_item = item.layout().takeAt(0)
                    if nested_item.widget():
                        nested_item.widget().deleteLater()
        
        # Получаем все объекты
        properties = self.session.query(Property).all()
        
        # Перебираем объекты в стандартном порядке для добавления слева направо
        for property in properties:
            # Создаем карточку
            card = QFrame()
            card.setFrameShape(QFrame.Shape.StyledPanel)
            card.setStyleSheet("""
                QFrame {
                    background-color: #2b2b2b;
                    border-radius: 10px;
                    padding: 15px;
                }
                QFrame[selected="true"] {
                     border: 2px solid #0d47a1;
                 }
                QFrame:hover {
                     background-color: #3d3d3d;
                 }
                QLabel {
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #0d47a1;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
            """)
            # card.setFixedWidth(250) # Удаляем фиксированную ширину карточки
            # card.setFixedHeight(250) # Удаляем фиксированную высоту карточки

            # Добавляем обработчик клика для выделения
            card.mousePressEvent = lambda event, card=card, p=property: self.select_property_card(card, p)
            card.setProperty("property_id", property.id) # Сохраняем ID объекта в свойство виджета
            
            # Создаем layout для карточки
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(10)
            
            # Верхняя часть с названием и статусом
            top_layout = QHBoxLayout()
            name_label = QLabel(property.name)
            name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            top_layout.addWidget(name_label)
            
            status_label = QLabel(property.status.value)
            status_label.setStyleSheet(f"""
                color: {'#4caf50' if property.status == PropertyStatus.AVAILABLE else '#f44336'};
                font-weight: bold;
            """)
            top_layout.addWidget(status_label)
            card_layout.addLayout(top_layout)
            
            # Информация об объекте
            info_layout = QVBoxLayout() # Оставляем общий вертикальный layout для информации
            info_layout.setSpacing(5) # Уменьшаем отступ между элементами информации
            
            # Горизонтальный layout для адреса, площади и этажа
            details_layout = QHBoxLayout()
            details_layout.setSpacing(10)
            
            address_label = QLabel(f"Адрес: {property.address}")
            area_label = QLabel(f"Площадь: {property.area} м²")
            floor_label = QLabel(f"Этаж: {property.floor}")
            
            details_layout.addWidget(address_label)
            details_layout.addWidget(area_label)
            details_layout.addWidget(floor_label)
            details_layout.addStretch() # Добавляем растягивающийся элемент
            
            info_layout.addLayout(details_layout)

            if property.description:
                description_label = QLabel(f"Описание: {property.description}")
                description_label.setWordWrap(True) # Включаем перенос слов
                info_layout.addWidget(description_label)
            
            card_layout.addLayout(info_layout)
            
            # Фотографии
            photos_layout = QHBoxLayout()
            photos_layout.setSpacing(10)  # Увеличиваем отступ между фотографиями
            
            # Получаем фотографии объекта
            photos = self.session.query(PropertyPhoto).filter(
                PropertyPhoto.property_id == property.id
            ).all()
            
            for photo in photos:
                photo_label = QLabel()
                pixmap = QPixmap(photo.file_path)
                photo_label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))  # Увеличиваем размер
                photo_label.setCursor(Qt.CursorShape.PointingHandCursor)  # Меняем курсор при наведении
                photo_label.setStyleSheet("""
                    QLabel {
                        border: 1px solid #3d3d3d;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QLabel:hover {
                        border: 1px solid #0d47a1;
                    }
                """)
                
                # Добавляем обработчик клика для открытия фото во весь экран
                photo_label.mousePressEvent = lambda event, path=photo.file_path: self.show_full_photo(property.id, path)
                photos_layout.addWidget(photo_label)
            
            if photos_layout.count() > 0:
                card_layout.addLayout(photos_layout)
            
            # Кнопки управления (теперь на карточке)
            buttons_layout = QHBoxLayout()

            edit_btn = QPushButton("Редактировать")
            edit_btn.clicked.connect(lambda checked, p=property: self.edit_property(p))
            buttons_layout.addWidget(edit_btn)

            delete_btn = QPushButton("Удалить")
            delete_btn.clicked.connect(lambda checked, p=property: self.delete_property(p))
            buttons_layout.addWidget(delete_btn)

            card_layout.addLayout(buttons_layout)
            
            # Добавляем карточку в вертикальный layout
            self.properties_layout.addWidget(card)
        
        # Добавляем растягивающийся элемент вниз
        self.properties_layout.addStretch()

    def select_property_card(self, card, property=None):
        # Снимаем выделение со всех карточек
        for widget in self.properties_container.findChildren(QFrame):
            widget.setProperty("selected", False)
            widget.setStyleSheet(widget.styleSheet()) # Обновляем стиль, чтобы снять выделение
        
        # Выделяем выбранную карточку
        card.setProperty("selected", True)
        card.setStyleSheet(card.styleSheet()) # Обновляем стиль, чтобы применить выделение
        self.selected_card = card  # Сохраняем выбранную карточку
        self.selected_property = property # Сохраняем выбранный объект

    def add_property(self):
        dialog = PropertyDialog(self)
        if dialog.exec():
            # Создаем новый объект
            property_data = dialog.get_property_data()
            property = Property(**property_data)
            self.session.add(property)
            self.session.commit()

            # Перемещаем временные фотографии в постоянную папку
            if dialog.temp_photos:
                photos_dir = f"photos/property_{property.id}"
                os.makedirs(photos_dir, exist_ok=True)
                
                for temp_photo in dialog.temp_photos:
                    new_file_name = f"{photos_dir}/{os.path.basename(temp_photo)}"
                    shutil.move(temp_photo, new_file_name)
                    
                    # Добавляем запись в базу
                    photo = PropertyPhoto(
                        property_id=property.id,
                        file_path=new_file_name,
                        description="",
                        is_main=0
                    )
                    self.session.add(photo)
                
                self.session.commit()

            self.load_properties()

    def edit_property(self, property):
        # Редактируем выбранный объект
        if property:
            # Получаем актуальный объект из базы перед редактированием
            property_to_edit = self.session.query(Property).get(property.id)
            dialog = PropertyDialog(self, property_to_edit)
            if dialog.exec():
                property_data = dialog.get_property_data()
                for key, value in property_data.items():
                    setattr(property_to_edit, key, value)
                self.session.commit()
                self.load_properties() # Обновляем список после сохранения

    def delete_property(self, property):
        # Удаляем выбранный объект
        if property:
            # Проверяем, можно ли удалить имущество
            if property.status.value == PropertyStatus.RENTED.value:
                QMessageBox.warning(self, "Ошибка", "Нельзя удалить имущество, которое сдано в аренду")
                return
                
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "Вы уверены, что хотите удалить это имущество?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.session.delete(property)
                self.session.commit()
                self.load_properties() # Обновляем список после удаления
                self.selected_card = None # Сбрасываем выбранную карточку
                self.selected_property = None # Сбрасываем выбранный объект

    def show_photos(self, property_id):
        # Находим объект по ID, так как show_photos вызывается напрямую из карточки
        property = self.session.query(Property).get(property_id)
        if property:
            dialog = PhotoDialog(property.id, self.session)
            if dialog.exec():
                self.load_properties()  # Перезагружаем список после изменений

    def show_full_photo(self, property_id, clicked_photo_path):
        """Открывает фотографию во весь экран для данного имущества с возможностью листания"""
        # Получаем все фотографии для данного имущества из базы
        photos = self.session.query(PropertyPhoto).filter(
            PropertyPhoto.property_id == property_id
        ).all()
        
        all_photo_paths = [p.file_path for p in photos if os.path.exists(p.file_path)]
        
        if not all_photo_paths:
            return

        # Находим индекс кликнутой фотографии
        try:
            current_index = all_photo_paths.index(clicked_photo_path)
        except ValueError:
            current_index = 0 # Если фото не найдено (что маловероятно), показываем первое

        # Открываем диалог просмотра
        dialog = PhotoViewerDialog(all_photo_paths, current_index, self)
        dialog.exec() 