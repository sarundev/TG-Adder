import threading
import time
import requests
import uvicorn
import csv
import os
import customtkinter as ctk
from tkinter import messagebox, filedialog
from server import app

API_BASE = "http://127.0.0.1:8000/api"

# High-Tech Theme Colors
BG_MAIN = "#0D1117"
BG_SIDEBAR = "#010409"
ACCENT_COLOR = "#00F0FF"
ACCENT_HOVER = "#00B8D4"
TEXT_COLOR = "#E6EDF3"
TEXT_MUTED = "#8B949E"
CARD_BG = "#161B22"

class HighTechApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TELE 168 - NEURAL COMMAND CENTER")
        self.geometry("1100x750")
        self.configure(fg_color=BG_MAIN)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ---------------- SIDEBAR ---------------- #
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=BG_SIDEBAR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        # Logo / Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, text="TELE 168", 
            font=ctk.CTkFont(family="Courier", size=26, weight="bold"),
            text_color=ACCENT_COLOR
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 5))
        
        self.sub_label = ctk.CTkLabel(
            self.sidebar_frame, text="SYSTEM INITIALIZED", 
            font=ctk.CTkFont(family="Courier", size=10),
            text_color=TEXT_MUTED
        )
        self.sub_label.grid(row=1, column=0, padx=20, pady=(0, 30))

        self.tab_buttons = []

        # Helper to create styled sidebar buttons
        def create_nav_btn(row, text, command):
            btn = ctk.CTkButton(
                self.sidebar_frame, text=text, command=command,
                font=ctk.CTkFont(family="Helvetica", size=14, weight="bold"),
                fg_color="transparent", text_color=TEXT_COLOR,
                hover_color=CARD_BG, corner_radius=8, anchor="w", height=40
            )
            btn.grid(row=row, column=0, padx=15, pady=5, sticky="ew")
            self.tab_buttons.append(btn)
            return btn

        self.btn_dashboard = create_nav_btn(2, "⚡  DASHBOARD", lambda: self.select_tab("⚡  DASHBOARD", self.show_dashboard))
        self.btn_add = create_nav_btn(3, "➕  ADD NODE", lambda: self.select_tab("➕  ADD NODE", self.show_add_account))
        self.btn_inviter = create_nav_btn(4, "🚀  MASS INJECTOR", lambda: self.select_tab("🚀  MASS INJECTOR", self.show_inviter))
        self.btn_join = create_nav_btn(5, "🔗  GROUP SYNC", lambda: self.select_tab("🔗  GROUP SYNC", self.show_join))
        self.btn_scraper = create_nav_btn(6, "📡  DATA SCRAPER", lambda: self.select_tab("📡  DATA SCRAPER", self.show_scraper))
        self.btn_g2g = create_nav_btn(7, "🔄  GROUP INJECTOR", lambda: self.select_tab("🔄  GROUP INJECTOR", self.show_group_inviter))

        # Status indicator at bottom
        self.status_indicator = ctk.CTkLabel(
            self.sidebar_frame, text="● SERVER ONLINE", 
            font=ctk.CTkFont(family="Courier", size=11, weight="bold"),
            text_color="#39FF14"
        )
        self.status_indicator.grid(row=9, column=0, pady=20)

        # ---------------- MAIN CONTENT ---------------- #
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=BG_MAIN)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.login_phone = ""
        self.login_hash = ""
        self.accounts = []
        self.scrape_cache_id = None

        # Start App
        self.select_tab("⚡  DASHBOARD", self.show_dashboard)

    def select_tab(self, name, func):
        for btn in self.tab_buttons:
            if btn.cget("text") == name:
                btn.configure(fg_color=CARD_BG, text_color=ACCENT_COLOR)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_COLOR)
        
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        func()

    def create_title(self, text):
        title = ctk.CTkLabel(
            self.main_frame, text=text, 
            font=ctk.CTkFont(family="Courier", size=28, weight="bold"),
            text_color=TEXT_COLOR
        )
        title.pack(pady=(20, 30), anchor="w", padx=40)
        
        # Glowing separator line
        sep = ctk.CTkFrame(self.main_frame, height=2, fg_color=ACCENT_COLOR, corner_radius=0)
        sep.pack(fill="x", padx=40, pady=(0, 20))

    def create_input(self, placeholder, is_password=False):
        return ctk.CTkEntry(
            self.main_frame, placeholder_text=placeholder,
            font=ctk.CTkFont(family="Helvetica", size=14),
            fg_color=CARD_BG, border_color=TEXT_MUTED, border_width=1,
            text_color=TEXT_COLOR, placeholder_text_color=TEXT_MUTED,
            corner_radius=8, height=45, show="*" if is_password else ""
        )

    def create_action_btn(self, text, command, color=ACCENT_COLOR, hover=ACCENT_HOVER, text_color="#000000"):
        return ctk.CTkButton(
            self.main_frame, text=text, command=command,
            font=ctk.CTkFont(family="Helvetica", size=14, weight="bold"),
            fg_color=color, hover_color=hover, text_color=text_color,
            corner_radius=8, height=45
        )

    # ---------- TABS ---------- #

    def show_dashboard(self):
        self.create_title("SYSTEM NODES (ACCOUNTS)")
        
        btn_refresh = self.create_action_btn("↻ REFRESH NETWORK STATUS", self.load_accounts)
        btn_refresh.pack(pady=10, padx=40, anchor="w")
        
        self.accounts_textbox = ctk.CTkTextbox(
            self.main_frame, font=ctk.CTkFont(family="Courier", size=13),
            fg_color=CARD_BG, text_color=ACCENT_COLOR, border_width=1, border_color=TEXT_MUTED,
            corner_radius=10
        )
        self.accounts_textbox.pack(pady=20, padx=40, fill="both", expand=True)
        self.load_accounts()

    def load_accounts(self):
        try:
            res = requests.get(f"{API_BASE}/accounts")
            if res.status_code == 200:
                self.accounts = res.json().get("accounts", [])
                text = ""
                for acc in self.accounts:
                    text += f"[ {acc} ] >> STATUS: ACTIVE\n"
                self.accounts_textbox.delete("1.0", "end")
                self.accounts_textbox.insert("1.0", text if text else ">> NO NODES FOUND IN NETWORK.")
        except Exception as e:
            self.accounts_textbox.delete("1.0", "end")
            self.accounts_textbox.insert("1.0", f">> CONNECTION ERROR: {e}")

    def show_add_account(self):
        self.create_title("INITIALIZE NEW NODE")

        self.phone_entry = self.create_input("Target Phone Number (+855...)")
        self.phone_entry.pack(pady=10, fill="x", padx=40)

        btn_req = self.create_action_btn("REQUEST OTP SECURE CODE", self.request_code, color="#1F6FEB", hover="#388BFD", text_color="#FFF")
        btn_req.pack(pady=10, padx=40, fill="x")

        self.code_entry = self.create_input("Enter OTP Code")
        self.code_entry.pack(pady=10, fill="x", padx=40)

        self.pwd_entry = self.create_input("2FA Password (Leave blank if none)", is_password=True)
        self.pwd_entry.pack(pady=10, fill="x", padx=40)

        btn_verify = self.create_action_btn("AUTHORIZE & CONNECT", self.verify_code)
        btn_verify.pack(pady=20, padx=40, fill="x")
        
        self.login_status = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Courier", size=14), text_color=ACCENT_COLOR)
        self.login_status.pack(pady=10)

    def request_code(self):
        phone = self.phone_entry.get().strip()
        if not phone: return
        self.login_status.configure(text=">> INITIATING HANDSHAKE...")
        try:
            res = requests.post(f"{API_BASE}/login/request_code", json={"phone": phone})
            if res.status_code == 200:
                data = res.json()
                self.login_hash = data.get("phone_code_hash", "")
                self.login_phone = phone
                self.login_status.configure(text=">> OTP SENT. WAITING FOR USER INPUT...")
            else:
                self.login_status.configure(text=f">> ERROR: {res.text}", text_color="#FF3333")
        except Exception as e:
            self.login_status.configure(text=f">> CRITICAL ERROR: {str(e)}", text_color="#FF3333")

    def verify_code(self):
        code = self.code_entry.get().strip()
        pwd = self.pwd_entry.get().strip()
        if not code or not self.login_phone: return
        self.login_status.configure(text=">> VERIFYING CREDENTIALS...")
        try:
            payload = {"phone": self.login_phone, "code": code, "phone_code_hash": self.login_hash, "password": pwd if pwd else None}
            res = requests.post(f"{API_BASE}/login/confirm", json=payload)
            if res.status_code == 200:
                self.login_status.configure(text=">> NODE AUTHORIZED SUCCESSFULLY.", text_color="#39FF14")
                self.load_accounts() # refresh accounts
            else:
                self.login_status.configure(text=f">> REJECTED: {res.text}", text_color="#FF3333")
        except Exception as e:
            self.login_status.configure(text=f">> CRITICAL ERROR: {str(e)}", text_color="#FF3333")

    def show_inviter(self):
        self.create_title("MASS INJECTOR PROTOCOL")
        
        self.invite_group_entry = self.create_input("Target Group ID (@groupname)")
        self.invite_group_entry.pack(pady=10, fill="x", padx=40)

        self.usernames_textbox = ctk.CTkTextbox(
            self.main_frame, font=ctk.CTkFont(family="Courier", size=13),
            fg_color=CARD_BG, text_color=TEXT_COLOR, border_width=1, border_color=TEXT_MUTED,
            corner_radius=10, height=120
        )
        self.usernames_textbox.pack(pady=10, fill="x", padx=40)
        self.usernames_textbox.insert("1.0", "@target1\n@target2\n+85571234567")
        
        self.delay_entry = self.create_input("Execution Delay Interval (Seconds)")
        self.delay_entry.insert(0, "15.0")
        self.delay_entry.pack(pady=10, fill="x", padx=40)

        btn_start = self.create_action_btn("▶ DEPLOY PAYLOAD (START INJECTING)", self.start_inviter, color="#39FF14", hover="#32CD32")
        btn_start.pack(pady=10, padx=40, fill="x")

        btn_stop = self.create_action_btn("■ ABORT PROTOCOL (EMERGENCY STOP)", self.stop_inviter, color="#FF003C", hover="#D90033", text_color="#FFF")
        btn_stop.pack(pady=5, padx=40, fill="x")
        
        self.inviter_status = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Courier", size=14), text_color=ACCENT_COLOR)
        self.inviter_status.pack(pady=10)

    def start_inviter(self):
        if not self.accounts:
            messagebox.showerror("SYSTEM ERROR", "NO NODES ACTIVE. NAVIGATE TO DASHBOARD.")
            return
            
        group = self.invite_group_entry.get().strip()
        usernames = self.usernames_textbox.get("1.0", "end-1c").split()
        delay = float(self.delay_entry.get() or 15)
        phones = self.accounts
        
        try:
            res = requests.post(f"{API_BASE}/inviter/invite-by-username", json={
                "accounts": phones, "target_group": group, "usernames": usernames, "delay": delay
            })
            if res.status_code == 200:
                self.inviter_status.configure(text=">> INJECTION TASK STARTED IN BACKGROUND.", text_color="#39FF14")
            else:
                self.inviter_status.configure(text=f">> FAILED: {res.text}", text_color="#FF3333")
        except Exception as e:
            self.inviter_status.configure(text=f">> CRITICAL ERROR: {str(e)}", text_color="#FF3333")

    def stop_inviter(self):
        try:
            requests.post(f"{API_BASE}/inviter/stop")
            self.inviter_status.configure(text=">> ABORT SIGNAL SENT. HALTING OPERATIONS.", text_color="#FF003C")
        except Exception as e:
            self.inviter_status.configure(text=f">> ERROR: {str(e)}", text_color="#FF3333")

    def show_join(self):
        self.create_title("GROUP SYNC MATRIX")
        
        self.join_group_entry = self.create_input("Target Group ID (@groupname or link)")
        self.join_group_entry.pack(pady=10, fill="x", padx=40)

        btn_start = self.create_action_btn("▶ SYNC ALL NODES TO GROUP", self.start_join)
        btn_start.pack(pady=20, padx=40, fill="x")
        
        self.join_status = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Courier", size=14))
        self.join_status.pack(pady=10)

    def start_join(self):
        if not self.accounts: return
        try:
            res = requests.post(f"{API_BASE}/join/start", json={
                "accounts": self.accounts,
                "target_group": self.join_group_entry.get().strip(),
                "delay": 15
            })
            if res.status_code == 200:
                self.join_status.configure(text=">> SYNC PROCESS STARTED.", text_color="#39FF14")
            else:
                self.join_status.configure(text=f">> ERROR: {res.text}", text_color="#FF3333")
        except Exception as e:
            self.join_status.configure(text=f">> CRITICAL ERROR: {str(e)}", text_color="#FF3333")

    def show_scraper(self):
        self.create_title("DATA SCRAPER")
        
        self.scrape_group_entry = self.create_input("Source Group ID (@groupname)")
        self.scrape_group_entry.pack(pady=10, fill="x", padx=40)
        
        # Checkbox for Only Usernames
        self.chk_usernames = ctk.CTkCheckBox(
            self.main_frame, text="Extract ONLY users with @usernames", 
            font=ctk.CTkFont(family="Helvetica", size=14),
            fg_color=ACCENT_COLOR, text_color=TEXT_COLOR
        )
        self.chk_usernames.select()
        self.chk_usernames.pack(pady=10, padx=40, anchor="w")

        btn_scrape = self.create_action_btn("▶ EXTRACT ENTITIES", self.start_scrape)
        btn_scrape.pack(pady=10, padx=40, fill="x")
        
        self.scrape_status = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Courier", size=14), text_color=ACCENT_COLOR)
        self.scrape_status.pack(pady=10)
        
        self.btn_export = self.create_action_btn("⬇ DOWNLOAD CSV", self.export_scrape, color="#1F6FEB", hover="#388BFD", text_color="#FFF")
        # Hidden initially
        
    def start_scrape(self):
        if not self.accounts:
            messagebox.showerror("SYSTEM ERROR", "NO NODES ACTIVE. NAVIGATE TO DASHBOARD.")
            return
            
        group = self.scrape_group_entry.get().strip()
        if not group: return
        
        self.scrape_status.configure(text=">> INITIATING SCRAPE... THIS MAY TAKE A MINUTE...", text_color=ACCENT_COLOR)
        self.btn_export.pack_forget()
        
        # Scrape runs synchronously in backend (it can take time, so we should run it in a thread to not freeze UI)
        def scrape_task():
            try:
                res = requests.post(f"{API_BASE}/scraper/scrape", json={
                    "account": self.accounts[0],
                    "group_url": group,
                    "filter_has_username": bool(self.chk_usernames.get()),
                    "filter_no_bots": True,
                    "filter_has_phone": False,
                    "filter_active_recently": False,
                    "filter_inactive": False,
                    "filter_has_name": False
                })
                if res.status_code == 200:
                    data = res.json()
                    self.scrape_cache_id = data.get("cache_id")
                    count = data.get("count", 0)
                    self.scrape_status.configure(text=f">> SUCCESS. EXTRACTED {count} ENTITIES.", text_color="#39FF14")
                    self.btn_export.pack(pady=10, padx=40, fill="x")
                else:
                    self.scrape_status.configure(text=f">> ERROR: {res.text}", text_color="#FF3333")
            except Exception as e:
                self.scrape_status.configure(text=f">> CRITICAL ERROR: {str(e)}", text_color="#FF3333")
                
        threading.Thread(target=scrape_task, daemon=True).start()

    def export_scrape(self):
        if not self.scrape_cache_id: return
        try:
            res = requests.get(f"{API_BASE}/scraper/export/{self.scrape_cache_id}")
            if res.status_code == 200:
                save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Save Scraped Data")
                if save_path:
                    with open(save_path, "wb") as f:
                        f.write(res.content)
                    self.scrape_status.configure(text=f">> EXPORT SAVED TO {save_path}", text_color="#39FF14")
        except Exception as e:
            self.scrape_status.configure(text=f">> ERROR SAVING CSV: {str(e)}", text_color="#FF3333")

    def show_group_inviter(self):
        self.create_title("GROUP TO GROUP INJECTOR")
        
        self.source_group_entry = self.create_input("Source Group ID (Scrape From)")
        self.source_group_entry.pack(pady=10, fill="x", padx=40)
        
        self.target_group_entry = self.create_input("Target Group ID (Inject To)")
        self.target_group_entry.pack(pady=10, fill="x", padx=40)
        
        self.delay_entry = self.create_input("Execution Delay Interval (Seconds)")
        self.delay_entry.insert(0, "15.0")
        self.delay_entry.pack(pady=10, fill="x", padx=40)

        btn_start = self.create_action_btn("▶ START GROUP-TO-GROUP INJECTION", self.start_group_inviter, color="#39FF14", hover="#32CD32")
        btn_start.pack(pady=20, padx=40, fill="x")
        
        btn_stop = self.create_action_btn("■ ABORT PROTOCOL (EMERGENCY STOP)", self.stop_inviter, color="#FF003C", hover="#D90033", text_color="#FFF")
        btn_stop.pack(pady=5, padx=40, fill="x")

        self.g2g_status = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Courier", size=14))
        self.g2g_status.pack(pady=10)

    def start_group_inviter(self):
        if not self.accounts:
            messagebox.showerror("SYSTEM ERROR", "NO NODES ACTIVE.")
            return
            
        source = self.source_group_entry.get().strip()
        target = self.target_group_entry.get().strip()
        delay = float(self.delay_entry.get() or 15)
        
        if not source or not target: return
        
        try:
            res = requests.post(f"{API_BASE}/inviter/invite-group", json={
                "accounts": self.accounts,
                "primary_account": self.accounts[0],
                "source_group": source,
                "target_group": target,
                "delay": delay
            })
            if res.status_code == 200:
                self.g2g_status.configure(text=">> GROUP INJECTION TASK STARTED.", text_color="#39FF14")
            else:
                self.g2g_status.configure(text=f">> ERROR: {res.text}", text_color="#FF3333")
        except Exception as e:
            self.g2g_status.configure(text=f">> CRITICAL ERROR: {str(e)}", text_color="#FF3333")

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == "__main__":
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    
    time.sleep(1.5)
    
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app_gui = HighTechApp()
    app_gui.mainloop()
