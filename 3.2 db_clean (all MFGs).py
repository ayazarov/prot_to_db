import sqlite3
import shutil
import re
from datetime import datetime

# Шаг 0: Копирование базы данных
source_db = '02 raw prots with separated test results.db'
destination_db = '03 only passed devices (cleared and separated).db'

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
            latest_row_date = datetime.strptime(latest_row[2], "%d.%m.%Y")
            latest_row_time = latest_row[3]

            for row in group[1:]:
                current_row_date = datetime.strptime(row[2], "%d.%m.%Y")
                current_row_time = row[3]

                # Сравниваем date
                if current_row_date != latest_row_date:
                    if current_row_date < latest_row_date:  # Более ранняя дата
                        print(f"Удалена строка с ROWID {row[4]}: {row} (дата {row[2]} старше, чем {latest_row[2]})")
                        cursor.execute(f"DELETE FROM {table_name} WHERE ROWID = ?", (row[4],))
                        deleted_rows_count += 1
                    else:
                        print(
                            f"Удалена строка с ROWID {latest_row[4]}: {latest_row} (дата {latest_row[2]} старше, чем {row[2]})")
                        cursor.execute(f"DELETE FROM {table_name} WHERE ROWID = ?", (latest_row[4],))
                        deleted_rows_count += 1
                        latest_row = row  # Обновляем latest_row
                        latest_row_date = current_row_date  # Обновляем дату
                        latest_row_time = current_row_time  # Обновляем время

                # Сравниваем time, если date одинаковые
                elif current_row_time != latest_row_time:
                    if current_row_time < latest_row_time:  # Более раннее время
                        print(f"Удалена строка с ROWID {row[4]}: {row} (время {row[3]} старше, чем {latest_row[3]})")
                        cursor.execute(f"DELETE FROM {table_name} WHERE ROWID = ?", (row[4],))
                        deleted_rows_count += 1
                    else:
                        print(
                            f"Удалена строка с ROWID {latest_row[4]}: {latest_row} (время {latest_row[3]} старше, чем {row[3]})")
                        cursor.execute(f"DELETE FROM {table_name} WHERE ROWID = ?", (latest_row[4],))
                        deleted_rows_count += 1
                        latest_row = row  # Обновляем latest_row
                        latest_row_date = current_row_date  # Обновляем дату
                        latest_row_time = current_row_time  # Обновляем время

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
        # cursor.execute(f"DELETE FROM {table_name} WHERE test_status NOT IN ('PASSED')")
        connection.commit()  # Сохраняем изменения после удаления

# Закрываем соединение с БД
connection.close()

print(f"Обработка завершена. Всего удаленных строк: {total_deleted_rows}")
