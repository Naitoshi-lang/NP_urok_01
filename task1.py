#Сервер часов
python
import socket
import time
from datetime import datetime
import threading

def time_server():
    # Создаем UDP сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Привязываем к порту
    server_address = ('', 12345)
    server_socket.bind(server_address)
    
    print(f"Сервер времени запущен на порту {server_address[1]}")
    print("Ожидание запросов времени...")
    
    while True:
        try:
            # Получаем запрос от клиента
            data, client_address = server_socket.recvfrom(1024)
            
            # Получаем текущее время
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Отправляем время клиенту
            server_socket.sendto(current_time.encode(), client_address)
            
            print(f"Отправлено время клиенту {client_address}: {current_time}")
            
        except KeyboardInterrupt:
            print("\nСервер остановлен")
            break
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    time_server()
#Клиент часов
python
import socket
import tkinter as tk
from tkinter import ttk
import threading

class ClockClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Сетевые часы")
        self.root.geometry("300x200")
        
        # Текущее время
        self.time_label = tk.Label(self.root, text="--:--:--", font=("Arial", 24))
        self.time_label.pack(pady=20)
        
        # Дата
        self.date_label = tk.Label(self.root, text="----/--/--", font=("Arial", 14))
        self.date_label.pack(pady=10)
        
        # Кнопка обновления
        self.update_btn = tk.Button(self.root, text="Обновить время", 
                                    command=self.update_time)
        self.update_btn.pack(pady=10)
        
        # Статус
        self.status_label = tk.Label(self.root, text="Готово")
        self.status_label.pack(pady=5)
        
        # Автообновление
        self.auto_update = tk.BooleanVar(value=True)
        self.auto_check = tk.Checkbutton(self.root, text="Автообновление (каждые 5 сек)",
                                         variable=self.auto_update)
        self.auto_check.pack(pady=5)
        
        # Параметры сервера
        self.server_ip = tk.StringVar(value="127.0.0.1")
        self.server_port = tk.IntVar(value=12345)
        
        settings_frame = tk.Frame(self.root)
        settings_frame.pack(pady=10)
        
        tk.Label(settings_frame, text="IP:").grid(row=0, column=0)
        tk.Entry(settings_frame, textvariable=self.server_ip, width=15).grid(row=0, column=1)
        
        tk.Label(settings_frame, text="Порт:").grid(row=1, column=0)
        tk.Entry(settings_frame, textvariable=self.server_port, width=10).grid(row=1, column=1)
        
        # Запускаем автообновление
        self.auto_update_time()
        
        self.root.mainloop()
    
    def get_time_from_server(self):
        try:
            # Создаем UDP сокет
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.settimeout(2)
            
            # Отправляем запрос на сервер
            server_address = (self.server_ip.get(), self.server_port.get())
            client_socket.sendto(b"time", server_address)
            
            # Получаем ответ
            data, _ = client_socket.recvfrom(1024)
            client_socket.close()
            
            return data.decode()
            
        except socket.timeout:
            return None
        except Exception as e:
            return f"Ошибка: {e}"
    
    def update_time(self):
        def update_task():
            self.update_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Запрос времени...")
            
            time_str = self.get_time_from_server()
            
            if time_str and not time_str.startswith("Ошибка"):
                # Формат: "2024-01-15 14:30:25"
                try:
                    date_part, time_part = time_str.split(" ")
                    self.date_label.config(text=date_part)
                    self.time_label.config(text=time_part)
                    self.status_label.config(text="Время обновлено")
                except:
                    self.time_label.config(text=time_str[:8])
                    self.status_label.config(text="Получено")
            else:
                self.status_label.config(text=time_str or "Нет ответа от сервера")
            
            self.update_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=update_task, daemon=True).start()
    
    def auto_update_time(self):
        if self.auto_update.get():
            self.update_time()
        
        # Планируем следующее обновление через 5 секунд
        self.root.after(5000, self.auto_update_time)

if __name__ == "__main__":
    ClockClient()
