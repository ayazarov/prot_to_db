import sqlite3
import pandas as pd
import numpy as np
import re

# Шаблонный список новых столбцов в структурированной БД
template_test_summary_columns = [
    "dw_ppm",
    # "lna_gain",
    # "lna_low",
    # "pwr_lna_low",
    "rtc_dw_ppm",
    "rtc_anc_ppm",
    # "rtc_ppm", это тоже, что и rtc_dw_ppm в старых логах
    # "rtc_tot_ppm", это тоже, что и rtc_anc_ppm в старых логах
    # "Vin",
    # "Vcc",
    # "Vbat",
    # "leak_dU/dt",
    # "leak_dU",
    # "leak_dt",
    # "pres",
    # "pres_Pa",
    # "pres_ofs_Pa",
    # "gnss_cno",
    # "gnss_rxed",
    # "gnss_used",
    # "profile",
    "skip_tests"
]


def preprocess_test_summary(test_summary):
    # Удаление пробелов и знаков в начале и конце строки
    cleaned_summary = test_summary.strip().lstrip('/ ').rstrip('.')

    # Удаление кавычек
    cleaned_summary = cleaned_summary.replace('"', '')

    return cleaned_summary


def parse_test_summary(test_summary):
    # Проверка, начинается ли строка с "/ " и не равна ли она "/ ."
    # "/ ." - это признак того, что тест даже не запустился
    # "/ " - это признак начала данных test_summary
    if not test_summary.startswith("/ ") or test_summary.strip() == "/ .":
        return {column: np.nan for column in template_test_summary_columns}

    # Предобработка строки
    cleaned_summary = preprocess_test_summary(test_summary)

    # Инициализация словаря для хранения результатов
    parsed_data = {column: np.nan for column in template_test_summary_columns}

    # Проверка, есть ли подстрока с "!"
    # "!" - это признак пропущенных тестов в test_summary
    if '!' in cleaned_summary:
        parts = cleaned_summary.split('!')
        # Записываем всё после "!" в skip_tests
        parsed_data['skip_tests'] = parts[1].strip() if len(parts) > 1 else np.nan
        cleaned_summary = parts[0].strip()  # Оставляем только первую часть

    # далее костыли для интерпретации некоторых данных, которые в разное время записывались в *.prot по-разному
    # проверка наличия записи "leak_dU/dt" и его обработка
    # start пока отключено, т.к. leak_dU/dt временно не нужно
    #leak_pattern = r'(?<!\w)(leak_dU/dt=)\s*([^@]+?)(?=\s+\w+\s*=|\s*$)'
    #leak_match = re.search(leak_pattern, cleaned_summary)
    """
    if leak_match:
        key, values = leak_match.groups()
        # Разделение значений
        leak_values = values.split('/')
        if len(leak_values) == 2:
            parsed_data['leak_dU'] = leak_values[0].strip()
            parsed_data['leak_dt'] = leak_values[1].strip()
        # Удаление записи "leak_dU/dt" из cleaned_summary
        cleaned_summary = re.sub(leak_pattern, '', cleaned_summary).strip()
    """
    # end пока отключено, т.к. leak_dU/dt временно не нужно

    # Разбитие строки на части, основываясь на ключах из template_test_summary_columns
    for column in template_test_summary_columns:
        # Шаблон для поиска точного совпадения ключа и его значения
        # этот pattern был до объединения rtc_ppm = rtc_dw_ppm, rtc_tot_ppm = rtc_anc_ppm
        # pattern = rf'(?<!\w)({re.escape(column)}=)([^@]+?)(?=\s+\w+\s*=|\s*$)'
        # это новый pattern
        pattern = rf'(?<!\w)({re.escape(column)}=)([^@]+?)(?=\s+\w+\s*=|\s*$)'
        match = re.search(pattern, cleaned_summary)

        ''' до объединения rtc_ppm = rtc_dw_ppm, rtc_tot_ppm = rtc_anc_ppm
        if match:
            key, value = match.groups()
            # Удаление лишних пробелов и сохранение значений
            parsed_data[column] = value.strip()
        '''
        if match:
            key, value = match.groups()
            value = value.strip()
            if column == "rtc_dw_ppm":              # перенаправление rtc_ppm
                parsed_data['rtc_dw_ppm'] = value
            elif column == "rtc_anc_ppm":           # перенаправление rtc_tot_ppm
                parsed_data['rtc_anc_ppm'] = value
            else:
                parsed_data[column] = value

    return parsed_data


def main():
    # Имена исходной и распарсеной БД
    source_db = '01 raw prots.db'
    target_db = '02 raw prots with separated test results.db'

    print(f'> welcome. now "{source_db}" will be parsed to separate test_summary string to separate columns')

    # Подключение к source_db
    try:
        conn_source = sqlite3.connect(source_db)
        print(f'> successful connection to the "{source_db}"')
    except sqlite3.Error as e:
        print(f'> error connection to "{source_db}": {e}')
    finally:
        if conn_source:
            # Получение списка всех таблиц, игнорируя системные таблицы
            tables = conn_source.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';").fetchall()
            table_names = [table[0] for table in tables]
            print(f'> tables in "{source_db}":')
            print(f'> {sorted(table_names)}')

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

                # Объединение исходных данные с новыми столбцами
                df = pd.concat([df, parsed_df], axis=1)

                # Сохранение результата в новую БД
                conn_target = sqlite3.connect(target_db)
                df.to_sql(table_name, conn_target, if_exists='replace', index=False)
                conn_target.close()

            conn_source.close()
    print(f'\n> parsing finished. results saved to "{target_db}"')


if __name__ == '__main__':
    main()
