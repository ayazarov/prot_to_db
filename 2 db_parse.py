import sqlite3
import pandas as pd
import numpy as np
import re

# Список новых столбцов
template_test_summary_columns = [
    "dw_ppm",
    "lna_gain",
    "lna_low",
    "pwr_lna_low",
    "rtc_dw_ppm",
    "rtc_anc_ppm",
    "rtc_ppm",
    "rtc_tot_ppm",
    "Vin",
    "Vcc",
    "Vbat",
    # "leak_dU/dt",
    "leak_dU",
    "leak_dt",
    "pres",
    "pres_Pa",
    "pres_ofs_Pa",
    "gnss_cno",
    "gnss_rxed",
    "gnss_used",
    "profile",
    "skip_tests"
]


def preprocess_test_summary(test_summary):
    # Убираем пробелы и знаки в начале и конце строки
    cleaned_summary = test_summary.strip().lstrip('/ ').rstrip('.')

    # Удаляем кавычки
    cleaned_summary = cleaned_summary.replace('"', '')

    return cleaned_summary


def parse_test_summary(test_summary):
    # Проверка, начинается ли строка с "/ " и не равна ли она "/ ."
    if not test_summary.startswith("/ ") or test_summary.strip() == "/ .":
        return {column: np.nan for column in template_test_summary_columns}

    # Предобработка строки
    cleaned_summary = preprocess_test_summary(test_summary)

    # Инициализируем словарь для хранения результатов
    parsed_data = {column: np.nan for column in template_test_summary_columns}

    # Проверяем, есть ли подстрока с "!"
    if '!' in cleaned_summary:
        parts = cleaned_summary.split('!')
        # Записываем всё после "!" в skip_tests
        parsed_data['skip_tests'] = parts[1].strip() if len(parts) > 1 else np.nan
        cleaned_summary = parts[0].strip()  # Оставляем только первую часть

    # Проверяем наличие leak_dU/dt и обрабатываем его
    leak_pattern = r'(?<!\w)(leak_dU/dt=)\s*([^@]+?)(?=\s+\w+\s*=|\s*$)'
    leak_match = re.search(leak_pattern, cleaned_summary)

    if leak_match:
        key, values = leak_match.groups()
        # Разделяем значения
        leak_values = values.split('/')
        if len(leak_values) == 2:
            parsed_data['leak_dU'] = leak_values[0].strip()
            parsed_data['leak_dt'] = leak_values[1].strip()
        # Удаляем leak_dU/dt из cleaned_summary
        cleaned_summary = re.sub(leak_pattern, '', cleaned_summary).strip()

    # Разбиваем строку на части, основываясь на ключах из template_test_summary_columns
    for column in template_test_summary_columns:
        # Шаблон для поиска точного совпадения ключа и его значения
        pattern = rf'(?<!\w)({re.escape(column)}=)([^@]+?)(?=\s+\w+\s*=|\s*$)'
        match = re.search(pattern, cleaned_summary)

        if match:
            key, value = match.groups()
            # Удаляем лишние пробелы и сохраняем значение
            parsed_data[column] = value.strip()

    return parsed_data


def main():
    # Имена исходной и распарсеной БД
    source_db = '01 raw prots.db'
    target_db = '02 raw prots with separated test results.db'

    # Подключение к исходной БД
    conn_source = sqlite3.connect(source_db)

    # Получение списка всех таблиц, игнорируя системные таблицы
    tables = conn_source.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';").fetchall()
    table_names = [table[0] for table in tables]

    for table_name in table_names:
        # Чтение данных из таблицы
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn_source)

        # Удаление пробелов в начале данных каждой ячейки
        df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

        # Проверка, есть ли хотя бы один столбец
        if df.empty or 'test_summary' not in df.columns:
            continue

        # Обработка столбца test_summary
        parsed_data = df['test_summary'].apply(parse_test_summary)
        parsed_df = pd.DataFrame(parsed_data.tolist())

        # Объединяем исходные данные с новыми столбцами
        df = pd.concat([df, parsed_df], axis=1)

        # Сохранение результата в новую БД
        conn_target = sqlite3.connect(target_db)
        df.to_sql(table_name, conn_target, if_exists='replace', index=False)
        conn_target.close()

    conn_source.close()


if __name__ == '__main__':
    main()
