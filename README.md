# Система управления арендой недвижимости

Система для управления арендой недвижимости, включающая функционал для работы с имуществом, договорами, платежами, арендаторами и документами.

## Функциональность

- Управление имуществом (добавление, редактирование, удаление объектов)
- Управление договорами аренды
- Учет платежей и формирование отчетов
- Управление арендаторами
- Работа с документами
- Аналитика и статистика
- Календарь событий

## Технологии

- Python 3.8+
- PyQt6 для GUI
- SQLAlchemy для работы с базой данных
- SQLite в качестве СУБД

## Установка

1. Клонировать репозиторий:
```bash
git clone https://github.com/your-username/rental-management-system.git
cd rental-management-system
```

2. Создать виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установить зависимости:
```bash
pip install -r requirements.txt
```

## Запуск

```bash
python main.py
```

## Структура проекта

```
rental-management-system/
├── core/                 # Ядро приложения
│   ├── database.py      # Модели базы данных
│   └── utils.py         # Утилиты
├── ui/                  # Пользовательский интерфейс
│   ├── main_window.py   # Главное окно
│   ├── property_widget.py
│   ├── contract_widget.py
│   └── ...
├── resources/           # Ресурсы (иконки, стили)
├── tests/              # Тесты
├── main.py             # Точка входа
└── requirements.txt    # Зависимости
```

## Лицензия

MIT 