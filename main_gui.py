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

# Modern Professional SaaS Theme Colors
BG_MAIN = "#121212"
BG_SIDEBAR = "#0A0A0A"
CARD_BG = "#1A1A1A"
CARD_BORDER = "#2A2A2A"

ACCENT_PRIMARY = "#4F46E5"    # Indigo 600
ACCENT_HOVER = "#4338CA"      # Indigo 700
ACCENT_SUCCESS = "#10B981"    # Emerald 500
ACCENT_DANGER = "#EF4444"     # Red 500
DANGER_HOVER = "#DC2626"      # Red 600

TEXT_PRIMARY = "#F9FAFB"      # Gray 50
TEXT_MUTED = "#9CA3AF"        # Gray 400

FONT_MAIN = "Helvetica"
FONT_TITLE = "Helvetica"

class ModernApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TG TELE168 Professional")
        self.geometry("1100x750")
        self.configure(fg_color=BG_MAIN)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ---------------- SIDEBAR ---------------- #
        self.sidebar_frame = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=BG_SIDEBAR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        # Logo / Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, text="TG TELE168", 
            font=ctk.CTkFont(family=FONT_TITLE, size=24, weight="bold"),
            text_color=ACCENT_PRIMARY
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(35, 2))
        
        self.sub_label = ctk.CTkLabel(
            self.sidebar_frame, text="Pro Automation Suite", 
            font=ctk.CTkFont(family=FONT_MAIN, size=12),
            text_color=TEXT_MUTED
        )
        self.sub_label.grid(row=1, column=0, padx=20, pady=(0, 40))

        self.tab_buttons = []

        # Helper to create styled sidebar buttons
        def create_nav_btn(row, text, command):
            btn = ctk.CTkButton(
                self.sidebar_frame, text=text, command=command,
                font=ctk.CTkFont(family=FONT_MAIN, size=15, weight="bold"),
                fg_color="transparent", text_color=TEXT_MUTED,
                hover_color=CARD_BG, corner_radius=8, anchor="w", height=45
            )
            btn.grid(row=row, column=0, padx=15, pady=6, sticky="ew")
            self.tab_buttons.append(btn)
            return btn

        self.btn_dashboard = create_nav_btn(2, "📊  Dashboard", lambda: self.select_tab("📊  Dashboard", self.show_dashboard))
        self.btn_add = create_nav_btn(3, "➕  Add Account", lambda: self.select_tab("➕  Add Account", self.show_add_account))
        self.btn_inviter = create_nav_btn(4, "🚀  Mass Inviter", lambda: self.select_tab("🚀  Mass Inviter", self.show_inviter))
        self.btn_join = create_nav_btn(5, "🔗  Join Group", lambda: self.select_tab("🔗  Join Group", self.show_join))
        self.btn_scraper = create_nav_btn(6, "📡  Data Scraper", lambda: self.select_tab("📡  Data Scraper", self.show_scraper))
        self.btn_g2g = create_nav_btn(7, "🔄  Group to Group", lambda: self.select_tab("🔄  Group to Group", self.show_group_inviter))
        self.btn_warmup = create_nav_btn(8, "🛡️  Account Warmup", lambda: self.select_tab("🛡️  Account Warmup", self.show_warmup))

        # Status indicator at bottom
        self.status_indicator = ctk.CTkLabel(
            self.sidebar_frame, text="● API Online & Connected", 
            font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            text_color=ACCENT_SUCCESS
        )
        self.status_indicator.grid(row=10, column=0, pady=30)

        # ---------------- MAIN CONTENT ---------------- #
        self.main_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=BG_MAIN)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)

        self.login_phone = ""
        self.login_hash = ""
        self.accounts = []
        self.scrape_cache_id = None

        # Start App
        self.select_tab("📊  Dashboard", self.show_dashboard)

    def select_tab(self, name, func):
        for btn in self.tab_buttons:
            if btn.cget("text") == name:
                btn.configure(fg_color=CARD_BG, text_color=ACCENT_PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED)
        
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        func()

    def create_title(self, text, subtitle=""):
        title = ctk.CTkLabel(
            self.main_frame, text=text, 
            font=ctk.CTkFont(family=FONT_TITLE, size=32, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        title.pack(pady=(30, 5), anchor="w", padx=40)
        
        if subtitle:
            sub = ctk.CTkLabel(
                self.main_frame, text=subtitle, 
                font=ctk.CTkFont(family=FONT_MAIN, size=14),
                text_color=TEXT_MUTED
            )
            sub.pack(pady=(0, 25), anchor="w", padx=40)
        else:
            sep = ctk.CTkFrame(self.main_frame, height=1, fg_color=CARD_BORDER, corner_radius=0)
            sep.pack(fill="x", padx=40, pady=(15, 25))

    def create_input(self, placeholder, is_password=False):
        return ctk.CTkEntry(
            self.main_frame, placeholder_text=placeholder,
            font=ctk.CTkFont(family=FONT_MAIN, size=14),
            fg_color=CARD_BG, border_color=CARD_BORDER, border_width=1,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_MUTED,
            corner_radius=8, height=48, show="*" if is_password else ""
        )

    def create_action_btn(self, text, command, color=ACCENT_PRIMARY, hover=ACCENT_HOVER, text_color="white", width=0):
        btn = ctk.CTkButton(
            self.main_frame, text=text, command=command,
            font=ctk.CTkFont(family=FONT_MAIN, size=14, weight="bold"),
            fg_color=color, hover_color=hover, text_color=text_color,
            corner_radius=8, height=45
        )
        if width > 0:
            btn.configure(width=width)
        return btn

    def create_status_label(self):
        lbl = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family=FONT_MAIN, size=14))
        lbl.pack(pady=10)
        return lbl

    def set_status(self, label, text, is_error=False, is_success=False):
        color = TEXT_PRIMARY
        if is_error: color = ACCENT_DANGER
        if is_success: color = ACCENT_SUCCESS
        label.configure(text=text, text_color=color)

    # ---------- DASHBOARD (ACCOUNTS LIST) ---------- #

    def show_dashboard(self):
        self.create_title("Dashboard", "Manage your connected Telegram accounts.")
        
        btn_refresh = self.create_action_btn("↻ Refresh Accounts", self.load_accounts, width=150)
        btn_refresh.pack(pady=5, padx=40, anchor="w")
        
        self.accounts_scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.accounts_scroll.pack(pady=20, padx=40, fill="both", expand=True)
        
        self.load_accounts()

    def load_accounts(self):
        for widget in self.accounts_scroll.winfo_children():
            widget.destroy()
            
        try:
            res = requests.get(f"{API_BASE}/accounts")
            if res.status_code == 200:
                self.accounts = res.json().get("accounts", [])
                
                if not self.accounts:
                    ctk.CTkLabel(self.accounts_scroll, text="No accounts connected. Go to 'Add Account' to begin.", text_color=TEXT_MUTED, font=ctk.CTkFont(size=14)).pack(pady=40)
                    return
                
                for acc in self.accounts:
                    # Account Card
                    card = ctk.CTkFrame(self.accounts_scroll, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=CARD_BORDER)
                    card.pack(fill="x", pady=8, padx=5)
                    
                    # Layout
                    left_box = ctk.CTkFrame(card, fg_color="transparent")
                    left_box.pack(side="left", padx=20, pady=15)
                    
                    # Phone
                    phone_lbl = ctk.CTkLabel(left_box, text=f"+{acc}", font=ctk.CTkFont(family=FONT_MAIN, size=16, weight="bold"), text_color=TEXT_PRIMARY)
                    phone_lbl.pack(anchor="w")
                    
                    # Status
                    status_lbl = ctk.CTkLabel(left_box, text="● Active & Ready", font=ctk.CTkFont(family=FONT_MAIN, size=12), text_color=ACCENT_SUCCESS)
                    status_lbl.pack(anchor="w", pady=(2,0))
                    
                    # Delete Button
                    btn_del = ctk.CTkButton(card, text="Delete", fg_color=ACCENT_DANGER, hover_color=DANGER_HOVER, width=80, height=32, corner_radius=6, command=lambda a=acc: self.delete_account(a))
                    btn_del.pack(side="right", padx=20)
                    
        except Exception as e:
            ctk.CTkLabel(self.accounts_scroll, text=f"Error connecting to backend: {e}", text_color=ACCENT_DANGER).pack(pady=20)

    def delete_account(self, phone):
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete +{phone}?"):
            try:
                requests.post(f"{API_BASE}/accounts/delete/{phone}")
                self.load_accounts()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ---------- ADD ACCOUNT ---------- #

    def show_add_account(self):
        self.create_title("Add New Account", "Connect a new Telegram node using OTP verification.")

        self.phone_entry = self.create_input("Phone Number (+1234567890)")
        self.phone_entry.pack(pady=10, fill="x", padx=40)

        btn_req = self.create_action_btn("Request Verification Code", self.request_code)
        btn_req.pack(pady=10, padx=40, fill="x")

        # Separator
        ctk.CTkFrame(self.main_frame, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=40, pady=20)

        self.code_entry = self.create_input("Enter 5-Digit Code")
        self.code_entry.pack(pady=10, fill="x", padx=40)

        self.pwd_entry = self.create_input("2FA Password (Optional)", is_password=True)
        self.pwd_entry.pack(pady=10, fill="x", padx=40)

        btn_verify = self.create_action_btn("Verify & Connect Account", self.verify_code, color=ACCENT_SUCCESS, hover="#059669")
        btn_verify.pack(pady=20, padx=40, fill="x")
        
        self.login_status = self.create_status_label()

    def request_code(self):
        phone = self.phone_entry.get().strip()
        if not phone: return
        self.set_status(self.login_status, "Requesting code from Telegram...")
        try:
            res = requests.post(f"{API_BASE}/accounts/login/request", json={"phone": phone})
            if res.status_code == 200:
                data = res.json()
                self.login_hash = data.get("phone_code_hash", "")
                self.login_phone = phone
                self.set_status(self.login_status, "OTP Code sent to your Telegram app!", is_success=True)
            else:
                self.set_status(self.login_status, f"Error: {res.text}", is_error=True)
        except Exception as e:
            self.set_status(self.login_status, f"Network Error: {e}", is_error=True)

    def verify_code(self):
        code = self.code_entry.get().strip()
        pwd = self.pwd_entry.get().strip()
        if not code or not self.login_phone: return
        self.set_status(self.login_status, "Verifying credentials...")
        try:
            payload = {"phone": self.login_phone, "code": code, "phone_code_hash": self.login_hash, "password": pwd if pwd else None}
            res = requests.post(f"{API_BASE}/accounts/login/confirm", json=payload)
            if res.status_code == 200:
                self.set_status(self.login_status, "Account successfully connected! Check Dashboard.", is_success=True)
                self.phone_entry.delete(0, 'end')
                self.code_entry.delete(0, 'end')
                self.pwd_entry.delete(0, 'end')
            else:
                self.set_status(self.login_status, f"Invalid Code/Password: {res.text}", is_error=True)
        except Exception as e:
            self.set_status(self.login_status, f"Network Error: {e}", is_error=True)

    # ---------- MASS INVITER ---------- #

    def show_inviter(self):
        self.create_title("Mass Inviter", "Inject a list of usernames into your target group.")
        
        self.invite_group_entry = self.create_input("Target Group (@groupname)")
        self.invite_group_entry.pack(pady=10, fill="x", padx=40)

        self.usernames_textbox = ctk.CTkTextbox(
            self.main_frame, font=ctk.CTkFont(family=FONT_MAIN, size=14),
            fg_color=CARD_BG, text_color=TEXT_PRIMARY, border_width=1, border_color=CARD_BORDER,
            corner_radius=8, height=120
        )
        self.usernames_textbox.pack(pady=10, fill="x", padx=40)
        self.usernames_textbox.insert("1.0", "Paste usernames here...\n@user1\n@user2")
        
        self.delay_entry = self.create_input("Delay Between Invites (Seconds)")
        self.delay_entry.insert(0, "15.0")
        self.delay_entry.pack(pady=10, fill="x", padx=40)

        btn_start = self.create_action_btn("Start Inviting", self.start_inviter)
        btn_start.pack(pady=15, padx=40, fill="x")

        btn_stop = self.create_action_btn("Stop All Invites", self.stop_inviter, color=ACCENT_DANGER, hover=DANGER_HOVER)
        btn_stop.pack(pady=5, padx=40, fill="x")
        
        self.inviter_status = self.create_status_label()

    def start_inviter(self):
        if not self.accounts:
            messagebox.showerror("Error", "No accounts available. Add accounts first.")
            return
            
        group = self.invite_group_entry.get().strip()
        usernames = self.usernames_textbox.get("1.0", "end-1c").split()
        delay = float(self.delay_entry.get() or 15)
        
        try:
            res = requests.post(f"{API_BASE}/inviter/invite-by-username", json={
                "accounts": self.accounts, "target_group": group, "usernames": usernames, "delay": delay
            })
            if res.status_code == 200:
                self.set_status(self.inviter_status, "Inviter task started successfully in background.", is_success=True)
            else:
                self.set_status(self.inviter_status, f"Failed: {res.text}", is_error=True)
        except Exception as e:
            self.set_status(self.inviter_status, f"Error: {e}", is_error=True)

    def stop_inviter(self):
        try:
            requests.post(f"{API_BASE}/inviter/stop")
            self.set_status(self.inviter_status, "Stop signal sent successfully.", is_success=True)
        except Exception as e:
            self.set_status(self.inviter_status, f"Error: {e}", is_error=True)

    # ---------- JOIN GROUP ---------- #

    def show_join(self):
        self.create_title("Join Group", "Force all your connected accounts to join a specific group.")
        
        self.join_group_entry = self.create_input("Target Group (@groupname or invite link)")
        self.join_group_entry.pack(pady=15, fill="x", padx=40)

        btn_start = self.create_action_btn("Join Group With All Accounts", self.start_join)
        btn_start.pack(pady=20, padx=40, fill="x")
        
        self.join_status = self.create_status_label()

    def start_join(self):
        if not self.accounts: return
        try:
            res = requests.post(f"{API_BASE}/join-group", json={
                "accounts": self.accounts,
                "target_group": self.join_group_entry.get().strip(),
                "delay": 15
            })
            if res.status_code == 200:
                self.set_status(self.join_status, "Join process started successfully.", is_success=True)
            else:
                self.set_status(self.join_status, f"Error: {res.text}", is_error=True)
        except Exception as e:
            self.set_status(self.join_status, f"Error: {e}", is_error=True)

    # ---------- DATA SCRAPER ---------- #

    def show_scraper(self):
        self.create_title("Data Scraper", "Extract members from public or private Telegram groups.")
        
        self.scrape_group_entry = self.create_input("Source Group (@groupname)")
        self.scrape_group_entry.pack(pady=15, fill="x", padx=40)
        
        self.chk_usernames = ctk.CTkCheckBox(
            self.main_frame, text="Extract ONLY users with @usernames (Recommended)", 
            font=ctk.CTkFont(family=FONT_MAIN, size=14),
            fg_color=ACCENT_PRIMARY, border_color=CARD_BORDER
        )
        self.chk_usernames.select()
        self.chk_usernames.pack(pady=15, padx=40, anchor="w")

        btn_scrape = self.create_action_btn("Start Scraping", self.start_scrape)
        btn_scrape.pack(pady=10, padx=40, fill="x")
        
        self.scrape_status = self.create_status_label()
        
        self.btn_export = self.create_action_btn("Download CSV", self.export_scrape, color=ACCENT_SUCCESS, hover="#059669")
        # Hidden initially
        
    def start_scrape(self):
        if not self.accounts:
            messagebox.showerror("Error", "No accounts available. Add accounts first.")
            return
            
        group = self.scrape_group_entry.get().strip()
        if not group: return
        
        self.set_status(self.scrape_status, "Scraping in progress... Please wait.")
        self.btn_export.pack_forget()
        
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
                    self.set_status(self.scrape_status, f"Success! Extracted {count} members.", is_success=True)
                    self.btn_export.pack(pady=15, padx=40, fill="x")
                else:
                    self.set_status(self.scrape_status, f"Error: {res.text}", is_error=True)
            except Exception as e:
                self.set_status(self.scrape_status, f"Error: {e}", is_error=True)
                
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
                    self.set_status(self.scrape_status, f"Export saved to {save_path}", is_success=True)
        except Exception as e:
            self.set_status(self.scrape_status, f"Export Error: {e}", is_error=True)

    # ---------- GROUP TO GROUP ---------- #

    def show_group_inviter(self):
        self.create_title("Group-to-Group Injector", "Scrape members from one group and instantly inject them into another.")
        
        self.source_group_entry = self.create_input("Source Group (Scrape From)")
        self.source_group_entry.pack(pady=10, fill="x", padx=40)
        
        self.target_group_entry = self.create_input("Target Group (Inject To)")
        self.target_group_entry.pack(pady=10, fill="x", padx=40)
        
        self.delay_entry = self.create_input("Delay Between Invites (Seconds)")
        self.delay_entry.insert(0, "15.0")
        self.delay_entry.pack(pady=10, fill="x", padx=40)

        btn_start = self.create_action_btn("Start Transfer", self.start_group_inviter)
        btn_start.pack(pady=20, padx=40, fill="x")
        
        btn_stop = self.create_action_btn("Stop Transfer", self.stop_inviter, color=ACCENT_DANGER, hover=DANGER_HOVER)
        btn_stop.pack(pady=5, padx=40, fill="x")

        self.g2g_status = self.create_status_label()

    def start_group_inviter(self):
        if not self.accounts:
            messagebox.showerror("Error", "No accounts available.")
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
                self.set_status(self.g2g_status, "Group injection task started successfully.", is_success=True)
            else:
                self.set_status(self.g2g_status, f"Error: {res.text}", is_error=True)
        except Exception as e:
            self.set_status(self.g2g_status, f"Error: {e}", is_error=True)

    # ---------- ACCOUNT WARMUP ---------- #

    def show_warmup(self):
        self.create_title("Account Warmup", "Simulate human behavior to prevent account bans.")
        
        self.warmup_status = self.create_status_label()

        btn_start = self.create_action_btn("Start Warmup (All Accounts)", self.start_warmup, color=ACCENT_SUCCESS, hover="#059669")
        btn_start.pack(pady=20, padx=40, fill="x")

    def start_warmup(self):
        if not self.accounts: return
        try:
            res = requests.post(f"{API_BASE}/warm/start", json={
                "accounts": self.accounts,
                "do_react": True, "do_chat": True, "reactions_per_group": 3, "messages_to_send": 3, "react_delay": 10.0, "chat_delay": 20.0
            })
            if res.status_code == 200:
                self.set_status(self.warmup_status, "Warmup task started successfully.", is_success=True)
            else:
                self.set_status(self.warmup_status, f"Error: {res.text}", is_error=True)
        except Exception as e:
            self.set_status(self.warmup_status, f"Error: {e}", is_error=True)


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == "__main__":
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    
    time.sleep(1.5)
    
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app_gui = ModernApp()
    app_gui.mainloop()
