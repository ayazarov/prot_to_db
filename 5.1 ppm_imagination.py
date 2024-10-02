import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

# Подключаемся к базе данных
conn = sqlite3.connect('03 only passed devices (cleared and separated).db')

# Загружаем данные из таблицы UwbTag
query = 'SELECT dw_ppm, rtc_dw_ppm FROM UwbTag'
df = pd.read_sql(query, conn)

# Закрываем соединение
conn.close()

# Убираем строки с текстовым "nan"
df = df[~df['dw_ppm'].isin(['nan']) & ~df['rtc_dw_ppm'].isin(['nan'])]

# Преобразуем столбцы в числовой формат
df['dw_ppm'] = pd.to_numeric(df['dw_ppm'], errors='coerce')
df['rtc_dw_ppm'] = pd.to_numeric(df['rtc_dw_ppm'], errors='coerce')

# Убираем строки с NaN
df = df.dropna(subset=['dw_ppm', 'rtc_dw_ppm'])  # Исправлено на 'rtc_dw_ppm'

# Создаем графики распределения
plt.figure(figsize=(12, 6))

# График для dw_ppm
plt.subplot(1, 2, 1)
hist_dw_ppm, bins_dw_ppm, _ = plt.hist(df['dw_ppm'], bins=50, color='blue', alpha=0.7)
plt.title('Распределение dw_ppm')
plt.xlabel('dw_ppm')
plt.ylabel('Частота')

# Установка меток по оси Y вручную, основываясь на максимальной частоте
max_frequency_dw_ppm = int(np.max(hist_dw_ppm))  # Максимальная частота
y_ticks = np.arange(0, max_frequency_dw_ppm + 1, step=1)  # Создание меток от 0 до максимума
plt.yticks(y_ticks)

# Установка меток по оси X
x_ticks = np.arange(np.floor(bins_dw_ppm[0]), np.ceil(bins_dw_ppm[-1]), step=1)  # Измените шаг при необходимости
plt.xticks(x_ticks, rotation=45, fontsize=8)

# Добавляем сетку
plt.grid(True)

# График для rtc_dw_ppm
plt.subplot(1, 2, 2)
hist_rtc_dw_ppm, bins_rtc_dw_ppm, _ = plt.hist(df['rtc_dw_ppm'], bins=50, color='green', alpha=0.7)
plt.title('Распределение rtc_dw_ppm')
plt.xlabel('rtc_dw_ppm')
plt.ylabel('Частота')

# Установка меток по оси Y вручную, основываясь на максимальной частоте
max_frequency_rtc_dw_ppM = int(np.max(hist_rtc_dw_ppm))  # Максимальная частота
y_ticks = np.arange(0, max_frequency_rtc_dw_ppM + 1, step=1)  # Создание меток от 0 до максимума
plt.yticks(y_ticks)

# Установка меток по оси X
x_ticks_rtc = np.arange(np.floor(bins_rtc_dw_ppm[0]), np.ceil(bins_rtc_dw_ppm[-1]), step=1)  # Измените шаг при необходимости
plt.xticks(x_ticks_rtc, rotation=45, fontsize=8)

# Добавляем сетку
plt.grid(True)

# Отображаем графики
plt.tight_layout()
plt.show()
