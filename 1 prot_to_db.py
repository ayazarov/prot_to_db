'''
        скрипт для добавления файла-протокола в БД as is

'''

import sys
import time
import sqlite3
import os


# изменение некоторых существительных при использовании с числами для сообщений, выводимых в консоль
def pluralize_noun(word, num):
    # словарь с окончаниями для разных слов
    # разные "секунды" здесь, тк могут использоваться как самостоятельно, так и во фрезе "через хх секунд"
    endings_dict = {
        "файл": {"singular": "", "plural_1": "а", "plural_2": "ов"},
        "секунда": {"singular": "а", "plural_1": "ы", "plural_2": ""},
        "секунд": {"singular": "у", "plural_1": "ы", "plural_2": ""},
    }

    # получение окончания для данного слова
    endings = endings_dict.get(word, {"singular": "", "plural_1": "", "plural_2": ""})

    # проверка на несколько основных случаев
    if num % 10 == 1 and num % 100 != 11:
        # 1 файл(), 21 файл(), 31 файл() и т.д.
        # 1 секунд(а), 21 секунд(а), 31 секунд(а) и т.д.
        # через 1 секунд(у) и т.д.
        result = f"{num} {word}{endings['singular']}"
    elif 2 <= num % 10 <= 4 and (num % 100 < 10 or num % 100 >= 20):
        # 2 файл(а), 3 файл(а), 4 файл(а), 22 файл(а), 23 файл(а) и т.д.
        # 2 секунд(ы), 3 секунд(ы), 4 секунд(ы), 22 секунд(ы), 23 секунд(ы) и т.д.
        # через 2 секунд(ы) и т.д.
        result = f"{num} {word}{endings['plural_1']}"
    else:
        # 0 файл(ов), 5 файл(ов), 6 файл(ов), 17 файл(ов), 28 файл(ов), 39 файл(ов) и т.д.
        # 0 секунд(), 6 секунд(), 37 секунд() и т.д.
        # через 6 секунд() и т.д.
        result = f"{num} {word}{endings['plural_2']}"

    return result


# вывод в консоль списка файлов с определенным разрешением в указанной директории
def list_files_with_extension(path, extension):
    file_list = [f for f in os.listdir(path) if f.endswith(extension)]
    file_dict = {num + 1: file_name for num, file_name in enumerate(file_list)}

    if file_dict:
        print(f"\tнайдено {pluralize_noun('файл', len(file_dict))} с расширением '*{extension}' в директории '{path}':")
        for num, file in file_dict.items():
            print(f'\t\t * [{num}] {file}')
    else:
        print(f"ошибка. в директории '{path}' нет файлов с расширением '*{extension}'.")

    return file_dict


# в любой непонятной ситуации дропнуть программу
def cancel_and_exit(wait_time_sec):
    for i in range(wait_time_sec, 0, -1):
        sys.stdout.write(f"\rпроцедура отменена. завершение программы через {pluralize_noun('секунд', i)}...")
        sys.stdout.flush()
        time.sleep(1)
    print("\nпрограмма завершена.")
    sys.exit()


# мини-парсинг строк файла-протокола (только по основным полям)
def parse_line(line):
    # разделение строки на дату и время по пробелу и остальные данные по запятой
    parts = line.strip().split(',')
    date, time = parts[0].split(' ')
    other_data = parts[1:]

    return date, time, *other_data


# создание файла БД
def create_new_DB_file(db_full_path):
    # подключение к БД
    conn = sqlite3.connect(db_full_path)
    # закрытие соединения
    conn.close()


# создание таблицы в БД с шаблонными столбцами файла-протокола
def create_table(cursor, table_name):
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            dev_type TEXT,
            HWID TEXT,
            SN TEXT,
            persBlock_checksum TEXT,
            CPU_ID TEXT,
            test_status TEXT,
            test_result TEXT,
            test_summary TEXT,
            UNIQUE(date, time, dev_type, HWID, SN, persBlock_checksum, CPU_ID)
        )
    ''')


# это основная функция, которая делает всю работу
# при импорте файла как модуля в итоге должна быть запущена именно она
def process_data(database_path, data_file_path, table_suffix):
    # подключение к БД
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    table_name = f'MFG_{table_suffix:02d}'

    # проверка существования таблицы с именем table_name
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    existing_table = cursor.fetchone()

    if existing_table is None:
        # cоздание новой таблицы в БД
        create_table(cursor, table_name)

    else:
        user_input = input(f"таблица с именем {table_name} уже существует в БД. что сделать?\n\tвведите 'ADD' для добавления данных в существующую таблицу, 'REMOVE' для удаления существующей таблицы с последующим созданием новой, 'CANCEL' для отмены редактирования БД. Ответ: ")

        if user_input.lower() == 'add':
            # заполнение таблицы данными из файла
            with open(data_file_path, 'r') as file:
                for line in file:
                    # парсинг строки и вставка данных в таблицу
                    data = parse_line(line)
                    try:
                        cursor.execute(f'''
                                INSERT INTO {table_name} (date, time, dev_type, HWID, SN, persBlock_checksum, CPU_ID, test_status, test_result, test_summary)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', data)
                        print(f"в таблицу {table_name} добавлена строка данных: {data}")
                    except sqlite3.IntegrityError as e:
                        print(f"ошибка при добавлении данных: {e}.\nстрока {data} уже существуют и не будет добавлена.")

        elif user_input.lower() == 'remove':
            # TODO сделать еще один запрос на подтверждение перед удалением для защиты
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            print(f"таблица {table_name} удалена из БД.")

            # создание новой таблицы после удаления предыдущей
            create_table(cursor, table_name)
            print(f"создана новая таблица {table_name} в БД.")

            # заполнение таблицы данными из файла
            with open(data_file_path, 'r') as file:
                for line in file:
                    # парсинг строки и вставка данных в таблицу
                    data = parse_line(line)
                    try:
                        cursor.execute(f'''
                                INSERT INTO {table_name} (date, time, dev_type, HWID, SN, persBlock_checksum, CPU_ID, test_status, test_result, test_summary)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', data)
                        print(f"в таблицу {table_name} добавлена строка данных: {data}")
                    except sqlite3.IntegrityError as e:
                        print(f"ошибка при добавлении данных: {e}. строка {data} уже существут и не будет добавлена.")

        elif user_input.lower() == 'cancel':
            # TODO дописать логику
            pass

        else:
            print("введенная команда некорректна. завершаемся")
            cancel_and_exit(3)

    # сохранение изменений в БД
    conn.commit()
    # закрытие соединения
    conn.close()



if __name__ == "__main__":
    # код, который будет выполнен при запуске файла напрямую.

    # при отмене операций или критичных ошибках программа вызывает функцию cancel_and_exit()
    # с параметром
    wait_time_sec = 3
    # если это неприемлемо - вносите изменения в нужные блоки

    # путь до папки со скриптом
    # нужен только здесь, тк используется только внутри функции choose_file()
    path_to_scripts_folder = os.path.dirname(os.path.abspath(__file__))

    # определим функцию, которая будет запрашивать пути до файлов
    # она нужна только здесь, тк при подключении файла как модуля, пути нужно передавать другим способом (через GUI, например)
    def choose_file(file_type, file_extension):
        # print(f"\n*** dbg msg старт функции 'choose_file'")

        file_full_path = None

        while file_full_path == None:
            file_path = input(f"\nукажите полный путь до файла {file_type} (с именем файла {file_type} и расширением *{file_extension}) или введите 'here', если файл {file_type} расположен в директории скрипта: ")

            # TODO реализовать проверку на ввод пути: до каталога или до файла

            file_num = None

            if file_path.lower() == 'here':
                file_dict = list_files_with_extension(path_to_scripts_folder, f'{file_extension}')
                if file_dict:
                    while True:
                        try:
                            file_num = int(input(f"введите номер требуемого файла {file_type} *{file_extension}, указанный в квадратных скобках: "))
                            # проверка, что введенный номер существует в словаре
                            if file_num not in file_dict:
                                print(f"ошибка: введенный номер не соответствует ни одному из найденных в каталоге файлов {file_type} *{file_extension}.")
                                continue  # repeat the loop

                            file_name = file_dict[file_num]
                            file_full_path = os.path.join(path_to_scripts_folder, file_name)
                            print(f"выбран файл {file_full_path}")
                            # break  # exit the loop
                            return file_full_path

                        except ValueError:
                            print("ошибка: введите корректное число.")
                            # continue the loop to ask for input again

                else:
                    # в указанной директории нет указанных файлов
                    print(f'*** dbg msg "в указанной директории нет указанного файла"')
                    # continue the loop to ask for input again

            elif file_type == 'БД' and not os.path.exists(file_path):
                # если проверяется файл БД и он НЕ существует по ПОЛНОМУ адресу, то
                user_input = input(f"ошибка. путь неверный или указанный файл {file_type} не существует. создать новый файл {file_type} с именем по умолчанию '{default_db_name}' в директории скрипта?\n\tвведите 'y' для подтверждения, 'n' для выхода из программы или любой символ для возврата к вводу пути. ")
                if user_input.lower() in ['y', 'yes']:
                    database_path = os.path.join(path_to_scripts_folder, default_db_name)
                    # если пользователь согласен на создание БД по умолчанию
                    # проверяем, есть ли такой файл в каталоге скрипта
                    if os.path.exists(database_path):
                        # файл БД с именем по умолчанию уже существует
                        user_input = input(f"файл '{default_db_name}' уже существует в директории {path_to_scripts_folder}. хотите удалить его и создать новый? (y/n): ").lower()
                        if user_input in ['y', 'yes']:
                            # даем запрос на удаление БД
                            os.remove(database_path)
                            if not os.path.exists(os.path.join(path_to_scripts_folder, default_db_name)):
                                # проверяем, удалился ли файл БД. если да, то
                                print(f"\nсуществующий файл '{default_db_name}' был успешно удален из каталога {path_to_scripts_folder}")
                            else:
                                print(f"\nошибка. невозможно удалить файл '{default_db_name}' из каталога {path_to_scripts_folder}")
                                # TODO обработать исключение, если надо. иначе просто завершить скрипт
                                cancel_and_exit(wait_time_sec)

                            # создание нового файла БД
                            create_new_DB_file(os.path.join(path_to_scripts_folder, default_db_name))

                            # проверяем, что БД создалась
                            if os.path.exists(database_path):
                                print(f"\nновый файл '{default_db_name}' был успешно создан в каталоге скрипта: {path_to_scripts_folder}")
                                # break  # exit the loop
                                return database_path
                            else:
                                print(f'\n ошибка. невозможно создать файл {file_type} {default_db_name} в каталоге скрипта: {path_to_scripts_folder}')
                                # continue  # repeat the loop
                                # TODO обработать исключение, если надо. иначе просто завершить скрипт
                                cancel_and_exit(wait_time_sec)

                        else:
                            print(f"\nсуществующий файл '{default_db_name}' не был изменен.")
                            # break  # exit the loop
                            return database_path

                    # пользователь согласен на создание БД по умолчанию
                    # и такого файла БД еще не существует в каталоге скрипта
                    else:
                        # создание нового файла БД
                        create_new_DB_file(os.path.join(path_to_scripts_folder, default_db_name))
                        # проверяем, что БД создалась
                        if os.path.exists(database_path):
                            print(f'\nфайл {file_type} {default_db_name} был успешно создан в каталоге скрипта: {path_to_scripts_folder}')
                            # break  # exit the loop
                            return database_path

                        else:
                            print(f'\n ошибка. невозможно создать файл {file_type} {default_db_name} в каталоге скрипта: {path_to_scripts_folder}')
                            # continue  # repeat the loop
                            # TODO обработать исключение, если надо. иначе просто завершить скрипт
                            cancel_and_exit(wait_time_sec)

                elif user_input.lower() in ['n', 'NO']:
                    cancel_and_exit(wait_time_sec)
                else:
                    print('*** dbg msg 1 DB section')
                    continue  # repeat the loop

            elif file_type == 'prot' and not os.path.exists(file_path):
                # если проверяется файл prot и он НЕ существует по ПОЛНОМУ адресу, то
                user_input = input(f"путь неверный или указанный файл {file_type}{file_extension} не существует.\n\tвведите 'n' для выхода из программы или любой символ для возврата к вводу пути. ")
                if user_input.lower() in ['n', 'NO']:
                    cancel_and_exit(wait_time_sec)
                else:
                    print('*** dbg msg 2 prot file section')
                    continue  # repeat the loop

        return file_full_path


    # имя файла БД, который создается по умолчанию
    default_db_name = "default_database.db"

    # проверка, ввел ли пользователь путь и/или существует ли файл БД по этому пути
    database_file_path = choose_file("БД", '.db')
    # print(f'*** dbg msg database_file_path: {database_file_path}')

    # проверка, ввел ли пользователь путь и/или существует ли файл данных по этому пути
    add_data_file_path = choose_file("протокола rtlsboot", '.prot')
    # print(f'*** dbg msg add_data_file_path: {add_data_file_path}')

    # требуем ввода номера производства, которому принадлежит *.prot файл
    while True:
        table_suffix = input('введите номер производства из диапазона [0..999]: ')
        try:
            # попытка преобразовать введенное значение в целое число
            mfg_number = int(table_suffix)
            # TODO когда-нибудь сделать недопустимым ввод номера уже закрытого производства
            # проверка, что введенное число является целым и не более 999
            if 0 <= mfg_number <= 999:
                # введенное значение допустимо
                break  # выход из цикла при корректном вводе
            else:
                print("ошибка. введите целое число из диапазона [0..999].")
        except ValueError:
            print("ошибка. введенные данные некорректны. введите целое число из диапазона [0..999].")

    # отрабатываем основную логику
    process_data(database_file_path, add_data_file_path, int(table_suffix))
