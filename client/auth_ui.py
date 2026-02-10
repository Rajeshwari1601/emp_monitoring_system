import tkinter as tk
from tkinter import messagebox
from api_client import APIClient
from config import Config

class AuthApp:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.api = APIClient()
        self.device_id = Config.get_device_id()
        self.device_name = Config.get_device_name()
        
        self.root.title("Client Agent Setup")
        self.root.geometry("300x400")
        
        self.show_login()

    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear_frame()
        
        tk.Label(self.root, text="Login", font=("Arial", 16)).pack(pady=20)
        
        tk.Label(self.root, text="Email").pack()
        self.email_entry = tk.Entry(self.root)
        self.email_entry.pack()
        
        tk.Label(self.root, text="Password").pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()
        
        tk.Button(self.root, text="Login", command=self.do_login).pack(pady=10)
        tk.Button(self.root, text="Register New Account", command=self.show_register).pack()

    def show_register(self):
        self.clear_frame()
        
        tk.Label(self.root, text="Register", font=("Arial", 16)).pack(pady=20)
        
        tk.Label(self.root, text="Name").pack()
        self.name_entry = tk.Entry(self.root)
        self.name_entry.pack()
        
        tk.Label(self.root, text="Email").pack()
        self.reg_email_entry = tk.Entry(self.root)
        self.reg_email_entry.pack()
        
        tk.Label(self.root, text="Password").pack()
        self.reg_password_entry = tk.Entry(self.root, show="*")
        self.reg_password_entry.pack()
        
        tk.Button(self.root, text="Register", command=self.do_register).pack(pady=10)
        tk.Button(self.root, text="Back to Login", command=self.show_login).pack()

    def do_login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        
        success, msg = self.api.login(email, password, self.device_id)
        if success:
            messagebox.showinfo("Success", "Login Successful")
            self.root.destroy()
            self.on_success()
        else:
            messagebox.showerror("Error", msg)

    def do_register(self):
        name = self.name_entry.get()
        email = self.reg_email_entry.get()
        password = self.reg_password_entry.get()
        
        success, msg = self.api.register(name, email, password, self.device_id, self.device_name)
        if success:
            messagebox.showinfo("Success", msg)
            self.show_login()
        else:
            messagebox.showerror("Error", msg)

def launch_auth_ui(on_success):
    root = tk.Tk()
    app = AuthApp(root, on_success)
    root.mainloop()
