import sqlite3
import shutil
import re

# Шаг 0: Копирование базы данных
source_db = 'target.db'
destination_db = 'tgt_cleared.db'

# Копируем файл базы данных
shutil.copyfile(source_db, destination_db)

# Функция для очистки таблицы
def clean_table(cursor, table_name):
    # Проверяем и добавляем новый столбец duplicates, если он не существует
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN duplicates TEXT")
    except sqlite3.OperationalError:
        pass  # Столбец уже существует

    # Шаг 1: Поиск дубликатов по CPU_ID
    cursor.execute(f"SELECT CPU_ID, SN, date, time, ROWID FROM {table_name}")
    rows = cursor.fetchall()

    duplicates = {}
    for row in rows:
        cpu_id, sn, date, time, row_id = row
        if cpu_id not in duplicates:
            duplicates[cpu_id] = []
        duplicates[cpu_id].append(row)

    # Счетчик удаленных строк
    deleted_rows_count = 0

    # Шаг 2: Обработка дубликатов по CPU_ID
    for cpu_id, group in duplicates.items():
        if len(group) > 1:  # Есть дубликаты
            sn_set = {row[1] for row in group}
            if len(sn_set) > 1:
                message = f"Дубликаты с CPU_ID {cpu_id} имеют разные SN: {sn_set}"
                print(message)
                for row in group:
                    cursor.execute(f"UPDATE {table_name} SET duplicates = ? WHERE ROWID = ?",
                                   (message, row[4]))
                continue  # Переход к следующей группе

            # Если SN одинаковые, продолжаем сравнение по date
            latest_row = group[0]
            for row in group[1:]:
                if row[2] != latest_row[2]:  # Сравниваем date
                    if row[2] > latest_row[2]:  # Более поздняя дата
                        print(f"Удалена строка с ROWID {latest_row[4]}: {latest_row}")
                        cursor.execute(f"DELETE FROM {table_name} WHERE ROWID = ?", (latest_row[4],))
                        deleted_rows_count += 1
                        latest_row = row
                    else:
                        print(f"Удалена строка с ROWID {row[4]}: {row}")
                        cursor.execute(f"DELETE FROM {table_name} WHERE ROWID = ?", (row[4],))
                        deleted_rows_count += 1

                elif row[3] != latest_row[3]:  # Сравниваем time, если date одинаковые
                    if row[3] > latest_row[3]:  # Более позднее время
                        print(f"Удалена строка с ROWID {latest_row[4]}: {latest_row}")
                        cursor.execute(f"DELETE FROM {table_name} WHERE ROWID = ?", (latest_row[4],))
                        deleted_rows_count += 1
                        latest_row = row
                    else:
                        print(f"Удалена строка с ROWID {row[4]}: {row}")
                        cursor.execute(f"DELETE FROM {table_name} WHERE ROWID = ?", (row[4],))
                        deleted_rows_count += 1

    # Сохраняем изменения
    return deleted_rows_count

# Подключаемся к новой базе данных
connection = sqlite3.connect(destination_db)
cursor = connection.cursor()

# Шаг 1: Получение списка всех таблиц
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Шаг 2: Обработка каждой таблицы с именем типа MFG_xx
total_deleted_rows = 0
for table in tables:
    table_name = table[0]
    if re.match(r'MFG_\d{1,3}$', table_name):  # Проверяем имя таблицы
        print(f"Обработка таблицы {table_name}...")
        deleted_rows = clean_table(cursor, table_name)
        total_deleted_rows += deleted_rows

# Шаг 3: Очистка пробелов и подсчет строк
for table in tables:
    table_name = table[0]
    if re.match(r'MFG_\d{1,3}$', table_name):  # Проверяем имя таблицы
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        # Получаем имена столбцов
        column_names = [description[0] for description in cursor.description]

        # Обновление строк в таблице
        for row in rows:
            updated_row = [str(cell).lstrip() for cell in row]
            set_clause = ', '.join([f"{col} = ?" for col in column_names])
            cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE rowid = ?", (*updated_row, row[0]))

# Сохраняем изменения
connection.commit()

# Подсчет общего количества строк
total_rows = 0
for table in tables:
    table_name = table[0]
    if re.match(r'MFG_\d{1,3}$', table_name):
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows += cursor.fetchone()[0]

print(f"Общее количество строк: {total_rows}")

# Удаление строк, где test_status не PASSED или TESTED
for table in tables:
    table_name = table[0]
    if re.match(r'MFG_\d{1,3}$', table_name):
        cursor.execute(f"DELETE FROM {table_name} WHERE test_status NOT IN ('PASSED', 'TESTED')")
        connection.commit()  # Сохраняем изменения после удаления

# Закрываем соединение с БД
connection.close()

print(f"Обработка дубликатов завершена. Всего удаленных строк: {total_deleted_rows}")
