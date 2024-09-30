import sqlite3
import pandas as pd
import re

# Задаем имя таблицы
table_name = 'MFG_21'

def parse_last_column(last_column):
    """Парсит строку с данными и возвращает словарь с ключами и значениями."""
    if last_column.strip() == '/':
        return {}

    # Регулярное выражение для парсинга ключ=значение
    pattern = r'(\w+)=("[^"]*"|\S+)'
    matches = re.findall(pattern, last_column)
    return {key: value.strip('"') for key, value in matches}


def main():
    # Подключение к исходной БД
    source_db = 'source.db'
    target_db = 'target.db'

    # Чтение данных из исходной БД
    conn_source = sqlite3.connect(source_db)
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn_source)
    conn_source.close()

    # Парсинг последнего столбца
    last_column_name = df.columns[-1]
    parsed_data = df[last_column_name].apply(parse_last_column)

    # Создание нового DataFrame с новыми столбцами
    parsed_df = pd.DataFrame(parsed_data.tolist())

    # Объединение с исходными данными (без последнего столбца)
    result_df = pd.concat([df.drop(columns=[last_column_name]), parsed_df], axis=1)

    # Сохранение результата в новую БД
    conn_target = sqlite3.connect(target_db)
    result_df.to_sql(table_name, conn_target, if_exists='replace', index=False)
    conn_target.close()


if __name__ == '__main__':
    main()
