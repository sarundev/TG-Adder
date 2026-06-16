import threading
import time
import requests
import json
import uvicorn
import customtkinter as ctk
from tkinter import messagebox
from server import app

API_BASE = "http://127.0.0.1:8000/api"

class TGTELE168App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TG TELE168")
        self.geometry("900x600")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="TG TELE168", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.tab_buttons = []
        self.current_frame = None

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=lambda: self.select_tab("Dashboard", self.show_dashboard))
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)
        self.tab_buttons.append(self.btn_dashboard)

        self.btn_add_account = ctk.CTkButton(self.sidebar_frame, text="Add Account", command=lambda: self.select_tab("Add Account", self.show_add_account))
        self.btn_add_account.grid(row=2, column=0, padx=20, pady=10)
        self.tab_buttons.append(self.btn_add_account)

        self.btn_inviter = ctk.CTkButton(self.sidebar_frame, text="Mass Inviter", command=lambda: self.select_tab("Mass Inviter", self.show_inviter))
        self.btn_inviter.grid(row=3, column=0, padx=20, pady=10)
        self.tab_buttons.append(self.btn_inviter)

        self.btn_join = ctk.CTkButton(self.sidebar_frame, text="Join Group", command=lambda: self.select_tab("Join Group", self.show_join))
        self.btn_join.grid(row=4, column=0, padx=20, pady=10)
        self.tab_buttons.append(self.btn_join)

        # Main Content Frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Start with Dashboard
        self.select_tab("Dashboard", self.show_dashboard)

        # Login state
        self.login_phone = ""
        self.login_hash = ""

        # Accounts cache
        self.accounts = []

    def select_tab(self, name, func):
        for btn in self.tab_buttons:
            if btn.cget("text") == name:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")
        
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        func()

    def show_dashboard(self):
        title = ctk.CTkLabel(self.main_frame, text="Dashboard", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=20)
        
        btn_refresh = ctk.CTkButton(self.main_frame, text="Refresh Accounts", command=self.load_accounts)
        btn_refresh.pack(pady=10)
        
        self.accounts_textbox = ctk.CTkTextbox(self.main_frame, width=600, height=400)
        self.accounts_textbox.pack(pady=10, fill="both", expand=True)
        
        self.load_accounts()

    def load_accounts(self):
        try:
            res = requests.get(f"{API_BASE}/accounts")
            if res.status_code == 200:
                self.accounts = res.json().get("accounts", [])
                text = ""
                for acc in self.accounts:
                    text += f"Phone: {acc['phone']} | Status: {acc.get('status', 'Unknown')}\n"
                self.accounts_textbox.delete("1.0", "end")
                self.accounts_textbox.insert("1.0", text if text else "No accounts found.")
        except Exception as e:
            self.accounts_textbox.delete("1.0", "end")
            self.accounts_textbox.insert("1.0", f"Error loading accounts: {e}")

    def show_add_account(self):
        title = ctk.CTkLabel(self.main_frame, text="Add New Account", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=20)

        self.phone_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Phone Number (+855...)")
        self.phone_entry.pack(pady=10, fill="x", padx=50)

        btn_req = ctk.CTkButton(self.main_frame, text="Request Code", command=self.request_code)
        btn_req.pack(pady=10)

        self.code_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Login Code")
        self.code_entry.pack(pady=10, fill="x", padx=50)

        self.pwd_entry = ctk.CTkEntry(self.main_frame, placeholder_text="2FA Password (if any)", show="*")
        self.pwd_entry.pack(pady=10, fill="x", padx=50)

        btn_verify = ctk.CTkButton(self.main_frame, text="Verify & Login", command=self.verify_code)
        btn_verify.pack(pady=10)
        
        self.login_status = ctk.CTkLabel(self.main_frame, text="")
        self.login_status.pack(pady=10)

    def request_code(self):
        phone = self.phone_entry.get().strip()
        if not phone: return
        self.login_status.configure(text="Requesting code...")
        try:
            res = requests.post(f"{API_BASE}/login/request_code", json={"phone": phone})
            if res.status_code == 200:
                data = res.json()
                self.login_hash = data.get("phone_code_hash", "")
                self.login_phone = phone
                self.login_status.configure(text="Code requested! Please enter it.")
            else:
                self.login_status.configure(text=res.text)
        except Exception as e:
            self.login_status.configure(text=str(e))

    def verify_code(self):
        code = self.code_entry.get().strip()
        pwd = self.pwd_entry.get().strip()
        if not code or not self.login_phone: return
        self.login_status.configure(text="Verifying...")
        try:
            payload = {
                "phone": self.login_phone,
                "code": code,
                "phone_code_hash": self.login_hash,
                "password": pwd if pwd else None
            }
            res = requests.post(f"{API_BASE}/login/confirm", json=payload)
            if res.status_code == 200:
                self.login_status.configure(text="Login Successful!")
            else:
                self.login_status.configure(text=res.text)
        except Exception as e:
            self.login_status.configure(text=str(e))

    def show_inviter(self):
        title = ctk.CTkLabel(self.main_frame, text="Mass Inviter (Usernames)", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=20)
        
        self.invite_group_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Target Group (@group)")
        self.invite_group_entry.pack(pady=10, fill="x", padx=50)

        self.usernames_textbox = ctk.CTkTextbox(self.main_frame, height=150)
        self.usernames_textbox.pack(pady=10, fill="x", padx=50)
        self.usernames_textbox.insert("1.0", "@username1\n@username2")
        
        self.delay_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Delay (seconds)")
        self.delay_entry.insert(0, "15")
        self.delay_entry.pack(pady=10, fill="x", padx=50)

        btn_start = ctk.CTkButton(self.main_frame, text="Start Inviting (All Accounts)", command=self.start_inviter)
        btn_start.pack(pady=10)

        btn_stop = ctk.CTkButton(self.main_frame, text="Stop Inviting", command=self.stop_inviter, fg_color="red")
        btn_stop.pack(pady=10)
        
        self.inviter_status = ctk.CTkLabel(self.main_frame, text="")
        self.inviter_status.pack(pady=10)

    def start_inviter(self):
        if not self.accounts:
            messagebox.showerror("Error", "No accounts available. Go to Dashboard to load them.")
            return
            
        group = self.invite_group_entry.get().strip()
        usernames = self.usernames_textbox.get("1.0", "end-1c").split()
        delay = float(self.delay_entry.get() or 15)
        
        phones = [acc["phone"] for acc in self.accounts]
        
        payload = {
            "accounts": phones,
            "target_group": group,
            "usernames": usernames,
            "delay": delay
        }
        try:
            res = requests.post(f"{API_BASE}/inviter/invite-by-username", json=payload)
            if res.status_code == 200:
                self.inviter_status.configure(text="Started successfully! Check terminal logs.")
            else:
                self.inviter_status.configure(text=res.text)
        except Exception as e:
            self.inviter_status.configure(text=str(e))

    def stop_inviter(self):
        try:
            requests.post(f"{API_BASE}/inviter/stop")
            self.inviter_status.configure(text="Stop signal sent!")
        except Exception as e:
            self.inviter_status.configure(text=str(e))

    def show_join(self):
        title = ctk.CTkLabel(self.main_frame, text="Join Group", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=20)
        
        self.join_group_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Target Group (@group)")
        self.join_group_entry.pack(pady=10, fill="x", padx=50)

        btn_start = ctk.CTkButton(self.main_frame, text="Join Group (All Accounts)", command=self.start_join)
        btn_start.pack(pady=10)
        
        self.join_status = ctk.CTkLabel(self.main_frame, text="")
        self.join_status.pack(pady=10)

    def start_join(self):
        if not self.accounts:
            return
        phones = [acc["phone"] for acc in self.accounts]
        payload = {
            "accounts": phones,
            "target_group": self.join_group_entry.get().strip(),
            "delay": 15
        }
        try:
            res = requests.post(f"{API_BASE}/join/start", json=payload)
            if res.status_code == 200:
                self.join_status.configure(text="Started successfully! Check terminal logs.")
            else:
                self.join_status.configure(text=res.text)
        except Exception as e:
            self.join_status.configure(text=str(e))

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == "__main__":
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    
    # Wait for server to boot
    time.sleep(2)
    
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app_gui = TGTELE168App()
    app_gui.mainloop()
