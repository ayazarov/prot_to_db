import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Подключаемся к базе данных
conn = sqlite3.connect('04 passed only devices (cleared and separated).db')

# Определяем значение HWID, по которому нужно фильтровать
hwid_value = 'AC7-POE'

# Загружаем данные из таблицы MFG_27 с фильтрацией по HWID
query = f"SELECT dw_ppm, rtc_dw_ppm FROM MFG_27 WHERE HWID = ?"
df = pd.read_sql(query, conn, params=(hwid_value,))

# Закрываем соединение
conn.close()

# Убираем строки с текстовым "nan"
df = df[~df['dw_ppm'].isin(['nan']) & ~df['rtc_dw_ppm'].isin(['nan'])]

# Преобразуем столбцы в числовой формат
df['dw_ppm'] = pd.to_numeric(df['dw_ppm'], errors='coerce')
df['rtc_dw_ppm'] = pd.to_numeric(df['rtc_dw_ppm'], errors='coerce')

# Убираем строки с NaN
df = df.dropna(subset=['dw_ppm', 'rtc_dw_ppm'])

# Создаем график с ящиками с усами
plt.figure(figsize=(12, 6))

# Ящик с усами для dw_ppm
plt.subplot(1, 2, 1)
plt.boxplot(df['dw_ppm'])
plt.title('Ящик с усами для dw_ppm')
plt.ylabel('dw_ppm')
plt.grid(True)

# Ящик с усами для rtc_dw_ppm
plt.subplot(1, 2, 2)
plt.boxplot(df['rtc_dw_ppm'])
plt.title('Ящик с усами для rtc_dw_ppm')
plt.ylabel('rtc_dw_ppm')
plt.grid(True)

# Настройка отображения
plt.tight_layout()
plt.show()

# Создаем фигуру с подграфиками
plt.figure(figsize=(12, 6))

# Сетчатая диаграмма для dw_ppm
plt.subplot(1, 2, 1)  # 1 строка, 2 колонки, 1 график
sns.violinplot(data=df['dw_ppm'], inner="quartile")
plt.title('Сетчатая диаграмма для dw_ppm')
plt.ylabel('dw_ppm')

# Изменяем параметры сетки
plt.grid(which='both', color='gray', linestyle='--', linewidth=0.7)

# Сетчатая диаграмма для rtc_dw_ppm
plt.subplot(1, 2, 2)  # 1 строка, 2 колонки, 2 график
sns.violinplot(data=df['rtc_dw_ppm'], inner="quartile")
plt.title('Сетчатая диаграмма для rtc_dw_ppm')
plt.ylabel('rtc_dw_ppm')

# Изменяем параметры сетки
plt.grid(which='both', color='gray', linestyle='--', linewidth=0.7)

# Настройка отображения
plt.tight_layout()
plt.show()

# Кумулятивная гистограмма для dw_ppm
plt.subplot(1, 2, 1)  # 1 строка, 2 колонки, 1 график
plt.hist(df['dw_ppm'], bins=50, cumulative=True, color='blue', alpha=0.7)
plt.title('Кумулятивная гистограмма для dw_ppm')
plt.xlabel('dw_ppm')
plt.ylabel('Кумулятивная частота')
plt.grid(True)

# Кумулятивная гистограмма для rtc_dw_ppm
plt.subplot(1, 2, 2)  # 1 строка, 2 колонки, 2 график
plt.hist(df['rtc_dw_ppm'], bins=50, cumulative=True, color='green', alpha=0.7)
plt.title('Кумулятивная гистограмма для rtc_dw_ppM')
plt.xlabel('rtc_dw_ppm')
plt.ylabel('Кумулятивная частота')
plt.grid(True)

# Настройка отображения
plt.tight_layout()
plt.show()


# Создаем фигуру с подграфиками
plt.figure(figsize=(12, 6))

# График частоты для dw_ppm
plt.subplot(1, 2, 1)  # 1 строка, 2 колонки, 1 график
counts_dw = df['dw_ppm'].value_counts().sort_index()
counts_dw.plot(kind='bar', color='blue', alpha=0.7)
plt.title('Частота значений dw_ppm')
plt.xlabel('Значение dw_ppm')
plt.ylabel('Частота')
plt.grid(True)

# Упрощаем метки по оси X
plt.xticks(ticks=range(0, len(counts_dw), max(1, len(counts_dw)//10)),
           labels=[f'{i}' for i in counts_dw.index[::max(1, len(counts_dw)//10)]], rotation=45)

# График частоты для rtc_dw_ppm
plt.subplot(1, 2, 2)  # 1 строка, 2 колонки, 2 график
counts_rtc = df['rtc_dw_ppm'].value_counts().sort_index()
counts_rtc.plot(kind='bar', color='green', alpha=0.7)
plt.title('Частота значений rtc_dw_ppM')
plt.xlabel('Значение rtc_dw_ppm')
plt.ylabel('Частота')
plt.grid(True)

# Упрощаем метки по оси X
plt.xticks(ticks=range(0, len(counts_rtc), max(1, len(counts_rtc)//10)),
           labels=[f'{i}' for i in counts_rtc.index[::max(1, len(counts_rtc)//10)]], rotation=45)

# Настройка отображения
plt.tight_layout()
plt.show()


# Создаем фигуру с подграфиками
plt.figure(figsize=(12, 6))

# График плотности для dw_ppm
plt.subplot(1, 2, 1)  # 1 строка, 2 колонки, 1 график
sns.kdeplot(df['dw_ppm'], color='blue', fill=True, alpha=0.5)
plt.title('Плотность распределения для dw_ppm')
plt.xlabel('Значение dw_ppm')
plt.ylabel('Плотность')
plt.grid(True)

# График плотности для rtc_dw_ppm
plt.subplot(1, 2, 2)  # 1 строка, 2 колонки, 2 график
sns.kdeplot(df['rtc_dw_ppm'], color='green', fill=True, alpha=0.5)
plt.title('Плотность распределения для rtc_dw_ppm')
plt.xlabel('Значение rtc_dw_ppm')
plt.ylabel('Плотность')
plt.grid(True)

# Настройка отображения
plt.tight_layout()
plt.show()



# Точечная диаграмма
plt.figure(figsize=(10, 5))
plt.scatter(df['dw_ppm'], df['rtc_dw_ppm'], alpha=0.5)
plt.title('Точечная диаграмма: dw_ppm vs rtc_dw_ppm')
plt.xlabel('dw_ppm')
plt.ylabel('rtc_dw_ppm')
plt.grid(True)
plt.show()