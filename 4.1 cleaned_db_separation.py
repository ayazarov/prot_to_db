import sqlite3

# Подключаемся к исходной базе данных
source_db = sqlite3.connect('target_cleared.db')
source_cursor = source_db.cursor()

# Задаем имя таблицы
table_name = 'MFG_27'

# Получаем уникальные значения dev_type
source_cursor.execute(f'SELECT DISTINCT dev_type FROM {table_name}')
unique_dev_types = [row[0] for row in source_cursor.fetchall()]

# Получаем описание таблицы {table_name} и выводим названия столбцов
source_cursor.execute(f'PRAGMA table_info({table_name})')
columns = [row[1] for row in source_cursor.fetchall() if row[1] != 'id']

# Выводим уникальные значения и названия столбцов в консоль
print("Уникальные значения dev_type:")
for dev_type in unique_dev_types:
    print(dev_type)

print("\nНазвания столбцов оригинальной таблицы (без ID):")
print(columns)

# Создаем новую базу данных
target_db = sqlite3.connect('target_separated.db')
target_cursor = target_db.cursor()

# Создаем таблицы для каждого уникального dev_type
for dev_type in unique_dev_types:
    target_cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS "{dev_type}" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {', '.join(columns)}
        )
    ''')

# Переносим данные из оригинальной таблицы в новые таблицы
for dev_type in unique_dev_types:
    source_cursor.execute(f'SELECT * FROM {table_name} WHERE dev_type = ?', (dev_type,))
    rows = source_cursor.fetchall()

    for row in rows:
        # Создаем запрос для вставки данных, исключая ID
        insert_query = f'INSERT INTO "{dev_type}" ({", ".join(columns)}) VALUES ({", ".join("?" for _ in columns)})'
        target_cursor.execute(insert_query, row[1:])  # row[1:] исключает ID

# Сохраняем изменения и закрываем базы данных
target_db.commit()
source_db.close()
target_db.close()
