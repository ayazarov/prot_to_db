import sqlite3
import matplotlib.pyplot as plt

db_name = "03 passed-tested devices (cleared and separated).db"  # Задайте имя вашей базы данных здесь


def collect_unique_hwid(conn):
    cursor = conn.cursor()
    hwid_count = {}

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f'список доступных таблиц в БД: {tables}')

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

    mfg_numbers = input("Введите номера MFG, разделенные запятой (например, 21, 27): ").split(',')
    mfg_numbers = [mfg.strip() for mfg in mfg_numbers]

    valid_mfg = [table.replace("MFG_", "") for table in counts.keys()]
    incorrect_mfg = [mfg for mfg in mfg_numbers if mfg not in valid_mfg]

    if incorrect_mfg:
        print(f"Некорректные номера MFG: {', '.join(incorrect_mfg)}. Попробуйте снова.")
    else:
        print(f"Выбраны MFG: {', '.join(mfg_numbers)}. Будет произведен анализ HWID: {hwid} из выбранных производств.")

        common_columns = get_columns_info(conn, counts, mfg_numbers)
        columns_display = '\n'.join(f"- {column}" for column in common_columns)
        chosen_column = input(f"\nВыберите один из столбцов для анализа:\n{columns_display}\nВведите имя столбца: ")
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

            plot_histograms(data, hwid, chosen_column)
        else:
            print(f"Некорректный выбор столбца. Доступные столбцы: {', '.join(common_columns)}")


def get_columns_info(conn, counts, mfg_numbers):
    excluded_columns = {"id", "date", "time", "dev_type", "HWID", "SN", "persBlock_checksum", "CPU_ID", "test_status",
                        "test_result"}
    common_columns = None

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

    return common_columns


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


def plot_histograms(data, hwid, column_name):
    table_data = {}
    table_counts = {}

    for entry in data:
        table = entry['table']
        value = entry['value']
        if table not in table_data:
            table_data[table] = []
            table_counts[table] = 0
        table_data[table].append(value)
        table_counts[table] += 1

    # Создание одного графика для всех таблиц
    plt.figure(figsize=(10, 5))
    for table, values in table_data.items():
        plt.hist(values, bins=50, alpha=0.5, label=f"{table} (Всего: {table_counts[table]})", density=True)

    plt.title(f'Гистограммы для {hwid} по производствам {", ".join(table_data.keys())}')
    plt.xlabel(f'{column_name}')

    # Обезличиваем ось Y
    plt.ylabel('')  # Убираем подпись оси Y
    plt.yticks([])  # Убираем метки на оси Y

    # plt.ylabel('Частота')
    plt.grid(axis='y', alpha=0.75)
    plt.axhline(0, color='black', linewidth=0.8)
    plt.legend()
    plt.show()


def main():
    try:
        conn = sqlite3.connect(db_name)

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
