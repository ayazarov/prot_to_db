import sqlite3
import shutil

# Шаг 0: Копирование базы данных
source_db = 'target.db'
destination_db = 'target_cleared.db'

# Копируем файл базы данных
shutil.copyfile(source_db, destination_db)

# Задаем имя таблицы
table_name = 'MFG_21'

# Шаг 1: Подключаемся к новой базе данных
connection = sqlite3.connect(destination_db)
cursor = connection.cursor()

# Проверяем и добавляем новый столбец duplicates, если он не существует
try:
    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN duplicates TEXT")
except sqlite3.OperationalError:
    pass  # Столбец уже существует

# Шаг 2: Поиск дубликатов по CPU_ID
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

# Шаг 3: Обработка дубликатов по CPU_ID
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

# Шаг 4: Поиск дубликатов по SN
cursor.execute(f"SELECT SN, CPU_ID, date, time, ROWID FROM {table_name}")
rows = cursor.fetchall()

sn_duplicates = {}
for row in rows:
    sn, cpu_id, date, time, row_id = row
    if sn not in sn_duplicates:
        sn_duplicates[sn] = []
    sn_duplicates[sn].append(row)

# Шаг 5: Обработка дубликатов по SN
for sn, group in sn_duplicates.items():
    if len(group) > 1:  # Есть дубликаты
        cpu_id_set = {row[1] for row in group}
        if len(cpu_id_set) > 1:
            message = f"Дубликаты с SN {sn} имеют разные CPU_ID: {cpu_id_set}"
            print(message)
            for row in group:
                cursor.execute(f"UPDATE {table_name} SET duplicates = ? WHERE ROWID = ?",
                               (message, row[4]))
            continue  # Переход к следующей группе

        # Если CPU_ID одинаковые, продолжаем сравнение по date
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

# Сохраняем изменения и закрываем соединение
connection.commit()
connection.close()

print(f"Обработка дубликатов завершена. Количество удаленных строк: {deleted_rows_count}")

'''-------=================----------'''

# Подключение к базе данных
conn = sqlite3.connect('target_cleared.db')
cursor = conn.cursor()

# 1. Удаление пробелов в начале текста в каждой ячейке построчно
cursor.execute(f"SELECT * FROM {table_name}")
rows = cursor.fetchall()

# Получаем имена столбцов
column_names = [description[0] for description in cursor.description]

# Обновление строк в таблице
for row in rows:
    updated_row = [str(cell).lstrip() for cell in row]
    set_clause = ', '.join([f"{col} = ?" for col in column_names])
    cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE rowid = ?", (*updated_row, row[0]))

conn.commit()  # Сохраняем изменения

# 2. Подсчет общего количества строк
cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
total_rows = cursor.fetchone()[0]
print(f"Общее количество строк: {total_rows}")

# Удаление строк, где test_status не PASSED или TESTED
cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE test_status NOT IN ('PASSED', 'TESTED')")
rows_to_delete = cursor.fetchone()[0]

cursor.execute(f"DELETE FROM {table_name} WHERE test_status NOT IN ('PASSED', 'TESTED')")
conn.commit()  # Сохраняем изменения

print(f"Количество удаленных строк: {rows_to_delete}")

# Закрываем соединение с БД
conn.close()
