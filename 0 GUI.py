import tkinter as tk
from tkinter import filedialog
from prot_to_db import process_data

def browse_file(entry, file_description, file_extension):
    filename = filedialog.askopenfilename(
        initialdir="/",
        title="Select a file",
        filetypes=((f"{file_description}", f"{file_extension}"), ("all files", "*.*"))
    )
    if filename:
        entry.config(state=tk.NORMAL)
        entry.delete(0, tk.END)
        entry.insert(0, filename)
        entry.config(state=tk.DISABLED)


def on_add_button_click():
    database_path = entry1.get()
    data_file_path = entry2.get()
    table_suffix = entry3.get()

    print("Database Path:", database_path)
    print("Data File Path:", data_file_path)
    print("Table Suffix:", table_suffix)

    try:
        table_suffix = int(table_suffix)
    except ValueError:
        print("Введите корректное целое число.")
    else:
        process_data(database_path, data_file_path, table_suffix)



# Создаем основное окно
root = tk.Tk()
root.title("Выбор файлов")

# Получаем размеры экрана
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Вычисляем координаты для центрирования окна
x_position = (screen_width - 400) // 2  # 400 - выбранная ширина окна
y_position = (screen_height - 350) // 2  # 200 - выбранная высота окна

# Устанавливаем размеры окна и его положение
root.geometry("400x100+{}+{}".format(x_position, y_position))

# Запрещаем изменение размеров окна
root.resizable(False, False)


root.columnconfigure(index=0, weight=1)
root.rowconfigure(index=0, weight=1)
label1 = tk.Label(root, text="DB file:")
label1.grid(row=0, column=0, padx=5, sticky=tk.W)
label2 = tk.Label(root, text="prot file:")
label2.grid(row=1, column=0, padx=5, sticky=tk.W)
label3 = tk.Label(root, text="MFG num:")
label3.grid(row=2, column=0, padx=5, sticky=tk.W)

root.columnconfigure(index=1, weight=6)
root.rowconfigure(index=1, weight=1)
entry1 = tk.Entry(root, state=tk.DISABLED)
entry1.grid(row=0, column=1, padx=(5, 0), sticky=tk.EW)
entry2 = tk.Entry(root, state=tk.DISABLED)
entry2.grid(row=1, column=1, padx=(5, 0), sticky=tk.EW)
entry3 = tk.Entry(root)
entry3.grid(row=2, column=1, padx=(5, 0), sticky=tk.W)
entry3.config(width=5)
label4 = tk.Label(root, text="int (0..100)")
label4.grid(row=2, column=1, padx=50, sticky=tk.W)

root.columnconfigure(index=2, weight=1)
root.rowconfigure(index=2, weight=1)
button1 = tk.Button(root, text="...", command=lambda: browse_file(entry1, "Database files", "*.db"))
button1.grid(row=0, column=2, padx=(0, 5))
button2 = tk.Button(root, text="...", command=lambda: browse_file(entry2, "prot files", "*.prot"))
button2.grid(row=1, column=2, padx=(0, 5))


root.rowconfigure(index=3, weight=1)
button_add = tk.Button(root, text="Add", command=on_add_button_click)
button_add.grid(row=3, column=1, pady=(5, 5))

# Запускаем цикл событий
root.mainloop()
