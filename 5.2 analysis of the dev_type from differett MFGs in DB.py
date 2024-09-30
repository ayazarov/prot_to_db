import sqlite3
import matplotlib.pyplot as plt

db_name = "tgt_cleared.db"  # Задайте имя вашей базы данных здесь


def remove_leading_spaces(conn):
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        print(f"Обрабатываем таблицу: {table_name}")

        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        for column in column_names:
            cursor.execute(f"SELECT rowid, {column} FROM {table_name};")
            rows = cursor.fetchall()

            for row in rows:
                rowid, value = row
                if isinstance(value, str):
                    new_value = value.lstrip()
                    cursor.execute(f"UPDATE {table_name} SET {column} = ? WHERE rowid = ?;", (new_value, rowid))

    conn.commit()
    print("Удаление пробелов завершено.")


def collect_unique_hwid(conn):
    cursor = conn.cursor()
    hwid_count = {}

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT HWID FROM {table_name};")
        hwids = cursor.fetchall()

        for hwid in hwids:
            hwid_value = hwid[0]
            if hwid_value:
                if hwid_value not in hwid_count:
                    hwid_count[hwid_value] = {}
                if table_name not in hwid_count[hwid_value]:
                    hwid_count[hwid_value][table_name] = 0
                hwid_count[hwid_value][table_name] += 1

    return hwid_count


def display_hwid_counts(hwid_count):
    sorted_hwid_count = sorted(hwid_count.items())

    for index, (hwid, counts) in enumerate(sorted_hwid_count, start=1):
        tables_info = " ; ".join([f"{table} - {count}" for table, count in counts.items()])
        print(f"[{index}] {hwid} ({tables_info})")
    return sorted_hwid_count


def analyze_selected_hwid(conn, hwid, hwid_count):
    counts = hwid_count[hwid]
    print(f"\nHWID: {hwid} встречается в следующих MFG таблицах:")
    for table, count in counts.items():
        print(f"{table} - {count}")

    mfg_numbers = input("Введите номера MFG (например, 21, 27), разделенные запятой: ").split(',')
    mfg_numbers = [mfg.strip() for mfg in mfg_numbers]

    valid_mfg = [table.replace("MFG_", "") for table in counts.keys()]
    incorrect_mfg = [mfg for mfg in mfg_numbers if mfg not in valid_mfg]

    if incorrect_mfg:
        print(f"Некорректные номера MFG: {', '.join(incorrect_mfg)}. Попробуйте снова.")
    else:
        print(f"Выбраны MFG: {', '.join(mfg_numbers)}. Будет произведен анализ HWID: {hwid} из выбранных MFG.")

        common_columns, unique_columns = get_columns_info(conn, counts, mfg_numbers)

        if common_columns:
            chosen_column = input(f"\nВыберите один из общих столбцов для анализа ({', '.join(common_columns)}): ")
            if chosen_column in common_columns:
                data, stats = analyze_column_data(conn, chosen_column, mfg_numbers, hwid)  # Передаем hwid
                print("\nДанные для построения гистограммы:")
                for entry in data:
                    print(f"Таблица: {entry['table']}, Значение: {entry['value']}")

                print("\nСтатистика по данным:")
                for table, (count, min_val, max_val) in stats.items():
                    if min_val is not None and max_val is not None:
                        print(f"{table}: Количество = {count}, Минимум = {min_val}, Максимум = {max_val}")
                    else:
                        print(f"{table}: Количество = {count}, Минимум/Максимум не определены.")

                plot_histograms(data)
            else:
                print(f"Некорректный выбор столбца. Доступные столбцы: {', '.join(common_columns)}")
        else:
            print("Нет общих столбцов для анализа.")


def get_columns_info(conn, counts, mfg_numbers):
    excluded_columns = {"id", "date", "time", "dev_type", "HWID", "SN", "persBlock_checksum", "CPU_ID", "test_status",
                        "test_result"}
    common_columns = None
    unique_columns = {}

    for mfg in mfg_numbers:
        table_name = f"MFG_{mfg}"
        if table_name in counts:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            column_names = {col[1] for col in columns} - excluded_columns

            if common_columns is None:
                common_columns = column_names
            else:
                common_columns &= column_names

            unique_columns[table_name] = column_names

    for table, columns in unique_columns.items():
        unique_columns[table] = columns - common_columns

    print("\nОбщие столбцы:")
    if common_columns:
        print(", ".join(common_columns))
    else:
        print("Нет общих столбцов.")

    print("\nУникальные столбцы:")
    for table, columns in unique_columns.items():
        if columns:
            print(f"{table}: {', '.join(columns)}")
        else:
            print(f"{table}: Нет уникальных столбцов.")

    return common_columns, unique_columns


def analyze_column_data(conn, column_name, mfg_numbers, hwid):
    results = []
    stats = {}
    for mfg in mfg_numbers:
        table_name = f"MFG_{mfg}"
        cursor = conn.cursor()
        # Добавляем условие WHERE для фильтрации по HWID
        cursor.execute(f"SELECT {column_name} FROM {table_name} WHERE HWID = ?;", (hwid,))
        data = cursor.fetchall()

        count = 0
        min_val = None
        max_val = None

        for row in data:
            value = row[0]
            if value is not None and value != "nan":
                try:
                    numeric_value = float(value)
                    results.append({'table': table_name, 'value': numeric_value})
                    count += 1
                    if min_val is None or numeric_value < min_val:
                        min_val = numeric_value
                    if max_val is None or numeric_value > max_val:
                        max_val = numeric_value
                except ValueError:
                    print(f"Не удалось преобразовать значение '{value}' в число.")

        stats[table_name] = (count, min_val, max_val)

    return results, stats


def plot_histograms(data):
    table_data = {}
    table_counts = {}  # Для хранения количества строк для каждой таблицы

    for entry in data:
        table = entry['table']
        value = entry['value']
        if table not in table_data:
            table_data[table] = []
            table_counts[table] = 0  # Инициализация счетчика для новой таблицы
        table_data[table].append(value)
        table_counts[table] += 1  # Увеличиваем счетчик для данной таблицы

    # Создание одного графика для всех таблиц
    plt.figure(figsize=(10, 5))
    for table, values in table_data.items():
        plt.hist(values, bins=30, alpha=0.5, label=f"{table} (Всего: {table_counts[table]})")

    plt.title('Гистограммы для выбранных MFG')
    plt.xlabel('Значения')
    plt.ylabel('Частота')
    plt.grid(axis='y', alpha=0.75)
    plt.axhline(0, color='black', linewidth=0.8)
    plt.legend()
    plt.show()


def main():
    try:
        conn = sqlite3.connect(db_name)
        remove_leading_spaces(conn)

        hwid_count = collect_unique_hwid(conn)
        sorted_hwid_count = display_hwid_counts(hwid_count)

        if len(sorted_hwid_count) == 0:
            print("Нет уникальных HWID в базе данных.")
            return

        while True:
            user_input = input("Введите номер из [] скобок для анализа HWID (или 'exit' для выхода): ")
            if user_input.lower() == 'exit':
                break

            try:
                index = int(user_input) - 1
                if 0 <= index < len(sorted_hwid_count):
                    hwid = sorted_hwid_count[index][0]
                    analyze_selected_hwid(conn, hwid, hwid_count)
                else:
                    print("Неправильный номер. Пожалуйста, попробуйте снова.")
            except ValueError:
                print("Некорректный ввод. Пожалуйста, введите номер.")

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
