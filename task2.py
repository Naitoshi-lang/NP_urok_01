#Сервер сообщений
import socket
import threading
import json
import time
from datetime import datetime

class MessageServer:
    def __init__(self, host='', port=12346):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
        # Хранилище сообщений: {получатель: [сообщения]}
        self.messages = {}
        self.clients = {}  # {addr: client_socket}
        
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        self.running = True
        print(f"Сервер сообщений запущен на {self.host}:{self.port}")
        print("Ожидание подключений...")
        
        try:
            while self.running:
                client_socket, client_address = self.server_socket.accept()
                print(f"Новое подключение: {client_address}")
                
                # Создаем поток для обработки клиента
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\nСервер остановлен")
        finally:
            self.stop()
    
    def handle_client(self, client_socket, client_address):
        try:
            while True:
                # Получаем данные от клиента
                data = client_socket.recv(4096).decode()
                if not data:
                    break
                
                try:
                    request = json.loads(data)
                    response = self.process_request(request)
                    
                    # Отправляем ответ
                    client_socket.send(json.dumps(response).encode())
                    
                except json.JSONDecodeError:
                    client_socket.send(json.dumps({
                        "status": "error",
                        "message": "Неверный формат запроса"
                    }).encode())
                
        except ConnectionError:
            print(f"Клиент {client_address} отключился")
        finally:
            client_socket.close()
            if client_address in self.clients:
                del self.clients[client_address]
    
    def process_request(self, request):
        action = request.get("action")
        
        if action == "send":
            return self.send_message(request)
        elif action == "get":
            return self.get_messages(request)
        elif action == "register":
            return self.register_client(request)
        else:
            return {"status": "error", "message": "Неизвестное действие"}
    
    def send_message(self, request):
        recipient = request.get("to")
        sender = request.get("from", "Аноним")
        text = request.get("text")
        
        if not recipient or not text:
            return {"status": "error", "message": "Не указан получатель или текст"}
        
        # Создаем сообщение
        message = {
            "from": sender,
            "text": text,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Сохраняем сообщение
        if recipient not in self.messages:
            self.messages[recipient] = []
        
        self.messages[recipient].append(message)
        
        print(f"Сообщение от {sender} для {recipient}: {text[:50]}...")
        
        return {
            "status": "success",
            "message": f"Сообщение отправлено {recipient}"
        }
    
    def get_messages(self, request):
        recipient = request.get("for")
        
        if not recipient:
            return {"status": "error", "message": "Не указан получатель"}
        
        if recipient in self.messages and self.messages[recipient]:
            messages = self.messages.pop(recipient)  # Забираем все сообщения
            return {
                "status": "success",
                "messages": messages
            }
        else:
            return {
                "status": "success",
                "messages": []
            }
    
    def register_client(self, request):
        client_name = request.get("name")
        if client_name:
            return {
                "status": "success",
                "message": f"Клиент {client_name} зарегистрирован"
            }
        else:
            return {"status": "error", "message": "Не указано имя"}
    
    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("Сервер остановлен")

if __name__ == "__main__":
    server = MessageServer()
    server.start()

#Клиент сообщений
import socket
import json
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading

class MessageClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Клиент сообщений")
        self.root.geometry("600x500")
        
        # Настройки соединения
        settings_frame = tk.Frame(self.root)
        settings_frame.pack(pady=10)
        
        tk.Label(settings_frame, text="Сервер:").grid(row=0, column=0)
        self.server_ip = tk.Entry(settings_frame, width=15)
        self.server_ip.insert(0, "127.0.0.1")
        self.server_ip.grid(row=0, column=1, padx=5)
        
        tk.Label(settings_frame, text="Порт:").grid(row=0, column=2)
        self.server_port = tk.Entry(settings_frame, width=10)
        self.server_port.insert(0, "12346")
        self.server_port.grid(row=0, column=3, padx=5)
        
        tk.Label(settings_frame, text="Ваше имя:").grid(row=1, column=0)
        self.user_name = tk.Entry(settings_frame, width=20)
        self.user_name.insert(0, "Пользователь")
        self.user_name.grid(row=1, column=1, columnspan=3, pady=5)
        
        # Вкладки
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Вкладка отправки
        self.send_frame = tk.Frame(self.notebook)
        self.notebook.add(self.send_frame, text="Отправить")
        
        tk.Label(self.send_frame, text="Кому:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.recipient = tk.Entry(self.send_frame, width=30)
        self.recipient.pack(padx=10, pady=(0, 10))
        
        tk.Label(self.send_frame, text="Сообщение:").pack(anchor=tk.W, padx=10)
        self.message_text = scrolledtext.ScrolledText(self.send_frame, height=10)
        self.message_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.send_btn = tk.Button(self.send_frame, text="Отправить", command=self.send_message)
        self.send_btn.pack(pady=10)
        
        # Вкладка получения
        self.receive_frame = tk.Frame(self.notebook)
        self.notebook.add(self.receive_frame, text="Получить")
        
        self.receive_btn = tk.Button(self.receive_frame, text="Проверить сообщения", 
                                     command=self.get_messages)
        self.receive_btn.pack(pady=10)
        
        self.messages_area = scrolledtext.ScrolledText(self.receive_frame, height=15)
        self.messages_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.messages_area.config(state=tk.DISABLED)
        
        # Статус
        self.status_label = tk.Label(self.root, text="Готово", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=10, pady=5)
        
        # Автопроверка сообщений
        self.auto_check = tk.BooleanVar(value=False)
        auto_check_btn = tk.Checkbutton(self.root, text="Автопроверка сообщений (каждые 10 сек)",
                                        variable=self.auto_check)
        auto_check_btn.pack(pady=5)
        
        self.root.after(10000, self.auto_check_messages)
        
        self.root.mainloop()
    
    def send_request(self, request):
        try:
            # Создаем TCP соединение
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            
            server_ip = self.server_ip.get()
            server_port = int(self.server_port.get())
            
            client_socket.connect((server_ip, server_port))
            
            # Отправляем запрос
            client_socket.send(json.dumps(request).encode())
            
            # Получаем ответ
            response_data = client_socket.recv(4096).decode()
            
            client_socket.close()
            
            return json.loads(response_data)
            
        except Exception as e:
            return {"status": "error", "message": f"Ошибка соединения: {e}"}
    
    def send_message(self):
        def send_task():
            self.send_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Отправка...")
            
            recipient = self.recipient.get().strip()
            text = self.message_text.get("1.0", tk.END).strip()
            
            if not recipient or not text:
                self.status_label.config(text="Заполните все поля")
                self.send_btn.config(state=tk.NORMAL)
                return
            
            request = {
                "action": "send",
                "from": self.user_name.get(),
                "to": recipient,
                "text": text
            }
            
            response = self.send_request(request)
            
            if response.get("status") == "success":
                self.status_label.config(text="Сообщение отправлено")
                self.message_text.delete("1.0", tk.END)
            else:
                self.status_label.config(text=f"Ошибка: {response.get('message')}")
            
            self.send_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=send_task, daemon=True).start()
    
    def get_messages(self):
        def get_task():
            self.receive_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Проверка сообщений...")
            
            request = {
                "action": "get",
                "for": self.user_name.get()
            }
            
            response = self.send_request(request)
            
            self.messages_area.config(state=tk.NORMAL)
            self.messages_area.delete("1.0", tk.END)
            
            if response.get("status") == "success":
                messages = response.get("messages", [])
                
                if messages:
                    for msg in messages:
                        sender = msg.get("from", "Неизвестно")
                        text = msg.get("text", "")
                        msg_time = msg.get("time", "")
                        
                        self.messages_area.insert(tk.END, 
                            f"[{msg_time}] {sender}:\n{text}\n{'='*50}\n")
                    
                    self.status_label.config(text=f"Получено {len(messages)} сообщений")
                else:
                    self.messages_area.insert(tk.END, "Нет новых сообщений")
                    self.status_label.config(text="Нет новых сообщений")
            else:
                self.messages_area.insert(tk.END, f"Ошибка: {response.get('message')}")
                self.status_label.config(text=f"Ошибка: {response.get('message')}")
            
            self.messages_area.config(state=tk.DISABLED)
            self.receive_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=get_task, daemon=True).start()
    
    def auto_check_messages(self):
        if self.auto_check.get():
            self.get_messages()
        
        # Планируем следующую проверку через 10 секунд
        self.root.after(10000, self.auto_check_messages)

if __name__ == "__main__":
    MessageClient()
