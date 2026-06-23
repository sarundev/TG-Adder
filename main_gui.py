import threading
import time
import requests
import uvicorn
import os
import subprocess
import uuid
import customtkinter as ctk
from tkinter import messagebox, filedialog
from server import app

# --- HOTFIX for CustomTkinter OptionMenu crash ---
_old_opt_destroy = ctk.CTkOptionMenu.destroy
def _safe_opt_destroy(self, *args, **kwargs):
    if not hasattr(self, '_variable'):
        self._variable = None
    try:
        _old_opt_destroy(self, *args, **kwargs)
    except Exception:
        pass
ctk.CTkOptionMenu.destroy = _safe_opt_destroy
# ------------------------------------------------

API_BASE         = "http://127.0.0.1:8000/api"
LICENSE_API_BASE = "https://web-production-89e12.up.railway.app/api"

# ═══════════════════════════════════════════
#   DESIGN TOKENS  —  Advanced Tech Tool
# ═══════════════════════════════════════════

C_BG          = "#0A0A0C"   # Deep Void Black
C_SIDEBAR     = "#121214"   # Dark Tech Sidebar
C_SURFACE     = "#18181B"   # Terminal Cards
C_SURFACE2    = "#27272A"   # Active states
C_BORDER      = "#3F3F46"   # Tech Borders

# Electric Neon Accents
C_CYAN        = "#00E5FF"   # Electric Cyan
C_CYAN_DIM    = "#003333"   # Dim Neon Glow
C_CYAN_HOVER  = "#18FFFF"

C_GOLD        = "#FFEA00"   # Neon Yellow
C_GOLD_DIM    = "#4D4D00"
C_GOLD_HOVER  = "#FFFF00"

C_GREEN       = "#00E676"   # Matrix Green
C_GREEN_DIM   = "#003311"

C_RED         = "#FF1744"   # Laser Red
C_RED_DIM     = "#4D0011"
C_RED_HOVER   = "#FF5252"

# Typography
C_TEXT        = "#FFFFFF"   # Pure White
C_TEXT2       = "#A1A1AA"   # Cyber Grey
C_TEXT3       = "#71717A"   # Muted Grey

SIDEBAR_W = 240
TOPBAR_H  = 64


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TELE168 PRO  ·  v1.0.1")
        self.geometry("1366x860")
        self.minsize(1100, 750)
        self.configure(fg_color=C_BG)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._state_init()
        self._build_topbar()
        self._build_sidebar()
        self._build_content()

        # Hide sidebar until licence verified
        self.sidebar.grid_remove()
        self.after(1500, self.check_license)

    # ─── state ────────────────────────────────
    def _state_init(self):
        self.hwid              = str(uuid.getnode())
        self.accounts          = []
        self.login_phone       = ""
        self.login_hash        = ""
        self.scrape_cache_id   = None
        self.is_terminal_active= False
        self._active_tab       = None
        self._nav_btns         = {}

    # ─── TOP BAR ──────────────────────────────
    def _build_topbar(self):
        bar = ctk.CTkFrame(
            self, height=TOPBAR_H, corner_radius=4,
            fg_color=C_BG, border_width=0
        )
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)

        # Left: logo
        logo_box = ctk.CTkFrame(bar, fg_color=C_SIDEBAR, width=SIDEBAR_W, corner_radius=4)
        logo_box.pack(side="left", fill="y")
        logo_box.pack_propagate(False)

        ctk.CTkLabel(
            logo_box,
            text=" TELE168 PRO",
            font=("Courier", 18, "bold"),
            text_color=C_TEXT
        ).place(relx=0.1, rely=0.5, anchor="w")

        # Right: tab name + version
        self.topbar_title = ctk.CTkLabel(
            bar, text="", font=("Courier", 18, "bold"),
            text_color=C_TEXT
        )
        self.topbar_title.pack(side="left", padx=40)

        # Search pill mock
        search_pill = ctk.CTkFrame(bar, width=280, height=36, corner_radius=4, fg_color=C_SURFACE)
        search_pill.pack(side="left", padx=20)
        search_pill.pack_propagate(False)
        ctk.CTkLabel(search_pill, text="⌕  Search...", text_color=C_TEXT3, font=("Courier", 12)).place(relx=0.08, rely=0.5, anchor="w")

        ctk.CTkLabel(
            bar, text="v1.0.1  ·  Professional",
            font=("Courier", 11, "bold"),
            text_color=C_CYAN
        ).pack(side="right", padx=30)

        # Bottom subtle line across full bar
        ctk.CTkFrame(
            self, height=1, corner_radius=4,
            fg_color=C_BORDER
        ).grid(row=0, column=0, columnspan=2, sticky="sew")

    # ─── SIDEBAR ──────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=SIDEBAR_W, corner_radius=4,
            fg_color=C_SIDEBAR, border_width=0
        )
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Thin right border
        ctk.CTkFrame(
            self.sidebar, width=1, corner_radius=4,
            fg_color=C_BORDER
        ).place(relx=1.0, rely=0, relheight=1, anchor="ne")

        ctk.CTkFrame(self.sidebar, height=16, fg_color="transparent").pack()

        nav = [
            ("Dashboard",        self.show_dashboard),
            ("Add Account",      self.show_add_account),
            ("Mass Inviter",     self.show_inviter),
            ("Join Group",       self.show_join),
            ("Data Scraper",     self.show_scraper),
            ("Group to Group",   self.show_group_inviter),
            ("Account Warmup",   self.show_warmup),
            ("Bot Starter",      self.show_bot_starter),
            ("Media Download",   self.show_media_downloader),
            ("Auto Poster",      self.show_video_poster),
            ("Promote to Admin", self.show_promote_admin),
            ("Update Tool",      self.show_updater),
        ]

        for name, func in nav:
            self._nav_btn(name, func)

        # Separator before terminal
        ctk.CTkFrame(self.sidebar, height=1, fg_color=C_BORDER).pack(
            fill="x", padx=16, pady=(16, 8)
        )
        self._nav_btn("Terminal Logs", self.show_terminal)

        # Bottom status area
        self._build_status_area()

    def _nav_btn(self, name, func):
        btn = ctk.CTkButton(
            self.sidebar,
            text=f"    {name}",
            command=lambda n=name, f=func: self._select(n, f),
            font=("Courier", 14),
            anchor="w",
            height=32,
            corner_radius=4,
            fg_color="transparent",
            hover_color=C_SURFACE2,
            text_color=C_TEXT2,
            border_width=0,
        )
        btn.pack(fill="x", padx=16, pady=3)
        self._nav_btns[name] = btn

    def _build_status_area(self):
        pill = ctk.CTkFrame(
            self.sidebar, fg_color="transparent"
        )
        pill.pack(fill="x", padx=16, pady=24, side="bottom")
        
        row = ctk.CTkFrame(pill, fg_color=C_CYAN_DIM, corner_radius=4, border_width=1, border_color=C_CYAN)
        row.pack(fill="x", ipady=12)

        dot = ctk.CTkFrame(row, width=8, height=8, corner_radius=4, fg_color=C_CYAN)
        dot.place(relx=0.15, rely=0.5, anchor="center")

        self._api_status_lbl = ctk.CTkLabel(
            row, text="API Connected",
            font=("Courier", 12, "bold"),
            text_color=C_CYAN
        )
        self._api_status_lbl.place(relx=0.25, rely=0.5, anchor="w")
        
        contact_lbl = ctk.CTkLabel(
            pill, text="Support: @sarun_chann",
            font=("Courier", 11), text_color=C_TEXT3
        )
        contact_lbl.pack(pady=(12, 0))

    # ─── CONTENT AREA ─────────────────────────
    def _build_content(self):
        self.content = ctk.CTkFrame(
            self, corner_radius=4, fg_color=C_BG
        )
        self.content.grid(row=1, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    # ─── TAB SWITCHING ────────────────────────
    def _select(self, name, func):
        self.is_terminal_active = (name == "Terminal Logs")
        self._active_tab = name
        self.topbar_title.configure(text=name)

        for n, b in self._nav_btns.items():
            if n == name:
                b.configure(
                    fg_color=C_CYAN_DIM, text_color=C_CYAN,
                    font=("Courier", 14, "bold"),
                    border_width=1, border_color="#006680"
                )
            else:
                b.configure(
                    fg_color="transparent", text_color=C_TEXT2,
                    font=("Courier", 14),
                    border_width=0
                )

        self.content.destroy()
        self._build_content()
        func()

    # ═══════════════════════════════════════════
    #   LICENSE SYSTEM
    # ═══════════════════════════════════════════
    def check_license(self):
        try:
            if not os.path.exists(".license_token"):
                self._show_license(); return
            with open(".license_token") as f:
                token = f.read().strip()
            if not token:
                self._show_license(); return
            r = requests.post(
                f"{LICENSE_API_BASE}/license/verify",
                json={"token": token, "hwid": self.hwid}, timeout=3
            )
            if r.status_code == 200:
                self._unlock(r.json())
            else:
                if os.path.exists(".license_token"):
                    os.remove(".license_token")
                self._show_license(error=r.json().get("detail", "License invalid or expired."))
        except Exception:
            self._show_license()
            
        if getattr(self, '_license_loop_started', False) is False:
            self._license_loop_started = True
            self.after(10000, self._real_time_license_check)

    def _real_time_license_check(self):
        threading.Thread(target=self._license_check_bg, daemon=True).start()
        self.after(10000, self._real_time_license_check)

    def _license_check_bg(self):
        if getattr(self, 'is_locked', False):
            return
        try:
            if not os.path.exists(".license_token"):
                self.after(0, self._show_license)
                return
            with open(".license_token") as f:
                token = f.read().strip()
            r = requests.post(f"{LICENSE_API_BASE}/license/verify", json={"token": token, "hwid": self.hwid}, timeout=5)
            if r.status_code != 200:
                if os.path.exists(".license_token"): os.remove(".license_token")
                try: err_msg = r.json().get("detail", "License invalid or expired.")
                except: err_msg = "License invalid or expired."
                self.after(0, self._show_license, err_msg)
        except Exception:
            pass
    def _unlock(self, data=None):
        self.is_locked = False
        self.sidebar.grid()
        self._select("Dashboard", self.show_dashboard)
        
        if data and hasattr(self, '_api_status_lbl'):
            days = data.get("duration_days")
            exp = data.get("expires_at")
            if days == 30:
                dur_text = "1 Month License"
            elif days == 1:
                dur_text = "1 Day License"
            elif days:
                dur_text = f"{days} Days License"
            else:
                dur_text = "Lifetime License"
                
            if exp:
                exp_date = exp.split("T")[0]
                self._api_status_lbl.configure(text=f"{dur_text} (Ends {exp_date})")
            else:
                self._api_status_lbl.configure(text=dur_text)

    def _show_license(self, error=""):
        self.is_locked = True
        self.sidebar.grid_remove() # Lock the user out of the app
        for w in self.content.winfo_children():
            w.destroy()

        # Premium Dark Background
        bg = ctk.CTkFrame(self.content, fg_color=C_BG, corner_radius=0)
        bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        CARD_W = 720
        CARD_H = 420
        
        # Main shadow card
        shadow = ctk.CTkFrame(bg, fg_color=C_BORDER, corner_radius=8, width=CARD_W+2, height=CARD_H+2)
        shadow.place(relx=0.5, rely=0.5, anchor="center")
        
        card = ctk.CTkFrame(shadow, width=CARD_W, height=CARD_H, fg_color=C_SURFACE, corner_radius=8)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.grid_propagate(False)
        card.pack_propagate(False)

        # ── Left Pane (Branding) ──
        left_pane = ctk.CTkFrame(card, width=280, height=CARD_H, fg_color=C_CYAN_DIM, corner_radius=0)
        left_pane.place(x=0, y=0)
        left_pane.pack_propagate(False)
        
        logo_ring = ctk.CTkFrame(left_pane, width=90, height=90, fg_color="transparent", border_width=2, border_color=C_CYAN, corner_radius=45)
        logo_ring.pack(pady=(100, 20))
        logo_ring.pack_propagate(False)
        
        # Professional Minimalist "T" Logo
        t_bar = ctk.CTkFrame(logo_ring, width=36, height=6, fg_color=C_CYAN, corner_radius=3)
        t_bar.place(relx=0.5, rely=0.35, anchor="center")
        t_stem = ctk.CTkFrame(logo_ring, width=6, height=32, fg_color=C_CYAN, corner_radius=3)
        t_stem.place(relx=0.5, rely=0.55, anchor="center")
        
        ctk.CTkLabel(left_pane, text="TELE168 PRO", font=("Courier", 24, "bold"), text_color=C_TEXT).pack(pady=(0, 4))
        ctk.CTkLabel(left_pane, text="Advanced Telegram Automation", font=("Courier", 12), text_color=C_CYAN).pack()
        
        contact_frame = ctk.CTkFrame(left_pane, fg_color="transparent")
        contact_frame.pack(side="bottom", pady=(0, 24))
        ctk.CTkLabel(contact_frame, text="24/7 SUPPORT", font=("Courier", 10, "bold"), text_color=C_TEXT3).pack()
        ctk.CTkLabel(contact_frame, text="Telegram: @sarun_chann", font=("Courier", 13, "bold"), text_color=C_TEXT).pack()
        
        ctk.CTkLabel(left_pane, text=f"HWID: {self.hwid}", font=("Courier", 10), text_color=C_TEXT3).pack(side="bottom", pady=16)

        # ── Right Pane (Form) ──
        right_pane = ctk.CTkFrame(card, width=CARD_W - 280, height=CARD_H, fg_color="transparent")
        right_pane.place(x=280, y=0)
        right_pane.pack_propagate(False)

        form_body = ctk.CTkFrame(right_pane, fg_color="transparent")
        form_body.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(form_body, text="Authenticate", font=("Courier", 28, "bold"), text_color=C_TEXT).pack(pady=(0, 8))
        ctk.CTkLabel(form_body, text="Please enter your secure license key.", font=("Courier", 14), text_color=C_TEXT2).pack(pady=(0, 12))

        if error:
            err_box = ctk.CTkFrame(form_body, fg_color=C_RED_DIM, corner_radius=6, border_width=1, border_color=C_RED)
            err_box.pack(fill="x", pady=(0, 20))
            ctk.CTkLabel(err_box, text=f"⚠️  {error}", font=("Courier", 13), text_color="#FFB3B3").pack(padx=16, pady=12)

        key_var = ctk.StringVar()
        key_entry = ctk.CTkEntry(
            form_body, textvariable=key_var, placeholder_text="TLG-XXXX-XXXX-XXXX",
            width=320, height=48, font=("Courier", 16, "bold"), justify="center",
            corner_radius=6, fg_color=C_BG, border_color=C_BORDER, border_width=2,
            text_color=C_TEXT, placeholder_text_color=C_TEXT3
        )
        key_entry.pack(pady=(0, 8))
        key_entry.focus_set()

        status = ctk.CTkLabel(form_body, text="", font=("Courier", 13, "bold"), text_color=C_TEXT2)
        status.pack(pady=(0, 16))

        def _activate():
            token = key_var.get().strip()
            if not token:
                status.configure(text="Please enter a license key.", text_color=C_RED)
                return
            status.configure(text="Verifying securely...", text_color=C_CYAN)
            self.update()
            try:
                r = requests.post(
                    f"{LICENSE_API_BASE}/license/verify",
                    json={"token": token, "hwid": self.hwid}, timeout=5
                )
                if r.status_code == 200:
                    with open(".license_token", "w") as f:
                        f.write(token)
                    status.configure(text="✓  Access Granted", text_color=C_GREEN)
                    self.update()
                    self.after(500, lambda: self._unlock(r.json()))
                else:
                    self._show_license(error=r.json().get("detail", "Invalid license."))
            except Exception as e:
                self._show_license(error="Could not reach license server.")

        key_entry.bind("<Return>", lambda e: _activate())

        btn = ctk.CTkButton(
            form_body, text="Activate Software", command=_activate,
            width=320, height=46, font=("Courier", 15, "bold"),
            corner_radius=6, fg_color=C_CYAN, hover_color=C_CYAN_HOVER, text_color=C_BG
        )
        btn.pack()

    # ═══════════════════════════════════════════
    #   PAGE BUILDING HELPERS
    # ═══════════════════════════════════════════
    def _scroll_frame(self):
        sf = ctk.CTkScrollableFrame(
            self.content, fg_color="transparent",
            scrollbar_button_color=C_BORDER, scrollbar_button_hover_color=C_SURFACE2
        )
        sf.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        sf.grid_columnconfigure(0, weight=1)
        return sf

    def _page_title(self, parent, subtitle=""):
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(32, 16))

        if subtitle:
            ctk.CTkLabel(
                hdr, text=subtitle,
                font=("Courier", 14),
                text_color=C_TEXT2, anchor="w"
            ).pack(anchor="w")

    def _section(self, parent, title=""):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="x", padx=40, pady=(16, 0))

        if title:
            ctk.CTkLabel(
                wrap, text=title,
                font=("Courier", 11, "bold"),
                text_color=C_TEXT3, anchor="w"
            ).pack(anchor="w", pady=(0, 8))

        card = ctk.CTkFrame(
            wrap, fg_color=C_SURFACE,
            corner_radius=8, border_width=1, border_color=C_BORDER
        )
        card.pack(fill="x")
        return card

    def _field(self, parent, label, placeholder, is_pw=False, default=""):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=(18, 0))

        ctk.CTkLabel(
            row, text=label,
            font=("Courier", 12, "bold"),
            text_color=C_TEXT2, anchor="w"
        ).pack(anchor="w", pady=(0, 6))

        e = ctk.CTkEntry(
            row, placeholder_text=placeholder,
            font=("Courier", 14), height=38,
            fg_color=C_BG, border_color=C_BORDER, border_width=1, corner_radius=6,
            text_color=C_TEXT, placeholder_text_color=C_TEXT3,
            show="•" if is_pw else ""
        )
        e.pack(fill="x")
        if default:
            e.insert(0, default)
        return e

    def _pad(self, parent, h=20):
        ctk.CTkFrame(parent, height=h, fg_color="transparent").pack()

    def _btn_primary(self, parent, text, cmd, pady=(20, 0)):
        b = ctk.CTkButton(
            parent, text=text, command=cmd,
            font=("Courier", 14, "bold"), fg_color=C_CYAN, hover_color=C_CYAN_HOVER,
            text_color=C_TEXT, corner_radius=6, height=42
        )
        b.pack(fill="x", padx=40, pady=pady)
        return b

    def _status_lbl(self, parent):
        lbl = ctk.CTkLabel(parent, text="", font=("Courier", 13), text_color=C_TEXT2)
        lbl.pack(pady=(12, 0))
        return lbl

    def _set_status(self, lbl, text, ok=False, err=False):
        color = C_TEXT2; pfx = ""
        if ok:  color = C_GREEN; pfx = "✓  "
        if err: color = C_RED;   pfx = "✕  "
        lbl.configure(text=f"{pfx}{text}", text_color=color)

    def _chk(self, parent, text, default=True, pady=(0, 0)):
        v = ctk.BooleanVar(value=default)
        c = ctk.CTkCheckBox(
            parent, text=text, variable=v,
            font=("Courier", 13), text_color=C_TEXT2,
            fg_color=C_CYAN, hover_color=C_CYAN_HOVER,
            border_color=C_BORDER, checkmark_color=C_BG, corner_radius=4
        )
        c.pack(anchor="w", padx=24, pady=pady)
        return v

    def _account_picker(self, parent, store_dict, label="SELECT ACCOUNTS"):
        card = self._section(parent, label)
        sf = ctk.CTkScrollableFrame(card, height=120, fg_color="transparent", scrollbar_button_color=C_BORDER)
        sf.pack(fill="x", padx=4, pady=8)
        if not self.accounts:
            ctk.CTkLabel(sf, text="No accounts connected.", text_color=C_TEXT3, font=("Courier", 13)).pack(pady=20)
        else:
            for acc in self.accounts:
                var = ctk.StringVar(value=acc)
                ctk.CTkCheckBox(
                    sf, text=f"  +{acc}", variable=var, onvalue=acc, offvalue="",
                    font=("Courier", 13), text_color=C_TEXT,
                    fg_color=C_CYAN, hover_color=C_CYAN_HOVER, border_color=C_BORDER, checkmark_color=C_BG
                ).pack(anchor="w", padx=18, pady=6)
                store_dict[acc] = var

    # ═══════════════════════════════════════════
    #   DASHBOARD
    # ═══════════════════════════════════════════
    def show_dashboard(self):
        sf = self._scroll_frame()
        self._page_title(sf, "Overview of your automation network.")

        # ── Stats row ──
        stats = ctk.CTkFrame(sf, fg_color="transparent")
        stats.pack(fill="x", padx=40, pady=(0, 20))
        for col in range(3):
            stats.grid_columnconfigure(col, weight=1)

        stat_data = [
            ("Total Accounts", str(len(self.accounts)) if self.accounts else "0", C_CYAN),
            ("Active Sessions", str(len(self.accounts)) if self.accounts else "0", C_GREEN),
            ("Server Status", "Online", C_GOLD),
        ]
        
        for i, (label, val, color) in enumerate(stat_data):
            c = ctk.CTkFrame(stats, fg_color=C_SURFACE, corner_radius=4, border_width=1, border_color=C_BORDER)
            c.grid(row=0, column=i, sticky="ew", padx=(0, 16 if i < 2 else 0))
            
            inner = ctk.CTkFrame(c, fg_color="transparent")
            inner.pack(padx=24, pady=24, anchor="w", fill="x")
            
            ctk.CTkLabel(inner, text=label, font=("Courier", 13), text_color=C_TEXT2).pack(anchor="w")
            ctk.CTkLabel(inner, text=val, font=("Courier", 18, "bold"), text_color=color).pack(anchor="w", pady=(4, 0))

        # ── Account list ──
        card = self._section(sf, "CONNECTED ACCOUNTS")
        
        # Header row for table
        h_row = ctk.CTkFrame(card, fg_color="transparent")
        h_row.pack(fill="x", padx=24, pady=(16, 8))
        ctk.CTkLabel(h_row, text="Account Number", font=("Courier", 11, "bold"), text_color=C_TEXT3).pack(side="left")
        ctk.CTkLabel(h_row, text="Status", font=("Courier", 11, "bold"), text_color=C_TEXT3).pack(side="right", padx=100)

        ctk.CTkFrame(card, height=1, fg_color=C_BORDER).pack(fill="x", padx=20)

        acc_sf = ctk.CTkScrollableFrame(card, fg_color="transparent", height=380, scrollbar_button_color=C_BORDER)
        acc_sf.pack(fill="both", padx=4, pady=8)

        self.load_accounts(acc_sf)
        
        # Refresh btn
        ctk.CTkButton(
            sf, text="↻ Refresh List", command=lambda: (self.load_accounts(acc_sf), None),
            font=("Courier", 13, "bold"), fg_color=C_SURFACE, hover_color=C_SURFACE2,
            text_color=C_TEXT, corner_radius=4, height=32, border_width=1, border_color=C_BORDER, width=140
        ).pack(anchor="e", padx=40, pady=(10, 20))

    def load_accounts(self, container):
        for w in container.winfo_children():
            w.destroy()
        try:
            r = requests.get(f"{API_BASE}/accounts")
            if r.status_code == 200:
                self.accounts = r.json().get("accounts", [])
                if not self.accounts:
                    ctk.CTkLabel(container, text="No accounts connected.", font=("Courier", 14), text_color=C_TEXT3).pack(pady=40)
                    return
                for i, acc in enumerate(self.accounts):
                    row = ctk.CTkFrame(container, fg_color="transparent")
                    row.pack(fill="x", padx=16, pady=4)

                    # Phone
                    phone_lbl = ctk.CTkLabel(row, text=f"+{acc}", font=("Courier", 15, "bold"), text_color=C_TEXT)
                    phone_lbl.pack(side="left", pady=12)

                    # Delete
                    ctk.CTkButton(
                        row, text="Remove", command=lambda a=acc: self._delete_account(a),
                        font=("Courier", 12, "bold"), width=80, height=32,
                        fg_color=C_RED_DIM, hover_color="#3A1010", text_color=C_RED, corner_radius=4,
                        border_width=1, border_color="#5A1515"
                    ).pack(side="right", padx=(20, 0))

                    # Status pill
                    pill = ctk.CTkFrame(row, fg_color=C_SURFACE2, corner_radius=4, border_width=1, border_color=C_BORDER)
                    pill.pack(side="right")
                    status_lbl = ctk.CTkLabel(pill, text="Checking...", font=("Courier", 11, "bold"), text_color=C_TEXT2)
                    status_lbl.pack(padx=12, pady=4)
                    
                    def check_status(a=acc, p=pill, l=status_lbl, p_lbl=phone_lbl):
                        try:
                            res = requests.get(f"{API_BASE}/accounts/check/{a}").json()
                            status = res.get("status", "Error")
                            name = res.get("name", "")
                            
                            if status == "Active":
                                self.after(0, lambda: p.configure(fg_color=C_GREEN_DIM, border_color="#164529"))
                                self.after(0, lambda: l.configure(text="Active", text_color=C_GREEN))
                                if name:
                                    self.after(0, lambda: p_lbl.configure(text=f"{name} (+{a})"))
                            elif status == "Expired":
                                self.after(0, lambda: p.configure(fg_color=C_RED_DIM, border_color="#5C2626"))
                                self.after(0, lambda: l.configure(text="Expired", text_color=C_RED))
                            else:
                                self.after(0, lambda: p.configure(fg_color=C_GOLD_DIM, border_color="#5C4D1D"))
                                self.after(0, lambda: l.configure(text="Error", text_color=C_GOLD))
                        except Exception:
                            self.after(0, lambda: p.configure(fg_color=C_GOLD_DIM, border_color="#5C4D1D"))
                            self.after(0, lambda: l.configure(text="Error", text_color=C_GOLD))

                    threading.Thread(target=check_status, daemon=True).start()
                    
                    ctk.CTkFrame(container, height=1, fg_color=C_BORDER).pack(fill="x", padx=16)

        except Exception as e:
            ctk.CTkLabel(container, text=f"Backend error: {e}", text_color=C_RED).pack(pady=20)

    def _delete_account(self, phone):
        if messagebox.askyesno("Delete Account", f"Permanently delete +{phone}?"):
            try:
                requests.post(f"{API_BASE}/accounts/delete/{phone}")
                self._select("Dashboard", self.show_dashboard)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ═══════════════════════════════════════════
    #   ADD ACCOUNT
    # ═══════════════════════════════════════════
    def show_add_account(self):
        sf = self._scroll_frame()
        self._page_title(sf, "Connect via OTP verification or import a TData archive.")

        otp_card = self._section(sf, "OTP VERIFICATION")
        self._phone_entry = self._field(otp_card, "Phone Number", "+1 234 567 8900")
        ctk.CTkButton(
            otp_card, text="Request Code", command=self._request_code,
            font=("Courier", 14, "bold"), height=32, corner_radius=4,
            fg_color=C_SURFACE2, hover_color=C_BORDER, text_color=C_TEXT, border_width=1, border_color=C_BORDER
        ).pack(fill="x", padx=24, pady=(16, 24))

        confirm_card = self._section(sf, "CONFIRM CODE")
        self._code_entry = self._field(confirm_card, "Verification Code", "5-digit code")
        self._pwd_entry  = self._field(confirm_card, "2FA Password (optional)", "Leave blank if none", is_pw=True)
        self._pad(confirm_card, 8)
        ctk.CTkButton(
            confirm_card, text="Verify & Connect", command=self._verify_code,
            font=("Courier", 14, "bold"), height=32, corner_radius=4,
            fg_color=C_CYAN_DIM, hover_color="#004D66", text_color=C_CYAN, border_width=1, border_color=C_CYAN
        ).pack(fill="x", padx=24, pady=(10, 24))

        td_card = self._section(sf, "IMPORT TDATA")
        ctk.CTkButton(
            td_card, text="Browse & Import TData (.zip)", command=self._upload_tdata,
            font=("Courier", 14, "bold"), height=32, corner_radius=4,
            fg_color=C_SURFACE2, hover_color=C_BORDER, text_color=C_TEXT, border_width=1, border_color=C_BORDER
        ).pack(fill="x", padx=24, pady=24)

        self._login_status = self._status_lbl(sf)
        self._pad(sf, 20)

    def _upload_tdata(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[("ZIP", "*.zip")], title="Select TData ZIP")
        if not path: return
        self._set_status(self._login_status, "Uploading & converting…")
        def task():
            try:
                with open(path, "rb") as f:
                    r = requests.post(f"{API_BASE}/accounts/upload-tdata-zip", files={"file": f})
                if r.status_code == 200:
                    ph = r.json().get("phone")
                    self.after(0, lambda: self._set_status(self._login_status, f"Account +{ph} added.", ok=True))
                else:
                    self.after(0, lambda: self._set_status(self._login_status, r.text, err=True))
            except Exception as e:
                self.after(0, lambda: self._set_status(self._login_status, str(e), err=True))
        threading.Thread(target=task, daemon=True).start()

    def _request_code(self):
        phone = self._phone_entry.get().strip()
        if not phone: return
        self._set_status(self._login_status, "Requesting code from Telegram…")
        try:
            r = requests.post(f"{API_BASE}/accounts/login/request", json={"phone": phone})
            if r.status_code == 200:
                d = r.json()
                self.login_hash  = d.get("phone_code_hash", "")
                self.login_phone = phone
                self._set_status(self._login_status, "Code sent to your Telegram app.", ok=True)
            else:
                self._set_status(self._login_status, r.text, err=True)
        except Exception as e:
            self._set_status(self._login_status, str(e), err=True)

    def _verify_code(self):
        code = self._code_entry.get().strip()
        pwd  = self._pwd_entry.get().strip()
        if not code or not self.login_phone: return
        self._set_status(self._login_status, "Verifying…")
        try:
            r = requests.post(f"{API_BASE}/accounts/login/confirm", json={
                "phone": self.login_phone, "code": code,
                "phone_code_hash": self.login_hash, "password": pwd or None
            })
            if r.status_code == 200:
                if r.json().get("status") == "password_required":
                    self._set_status(self._login_status, "2FA required — enter password and verify again.", err=True)
                else:
                    self._set_status(self._login_status, "Account connected. Check Dashboard.", ok=True)
                    for e in (self._phone_entry, self._code_entry, self._pwd_entry): e.delete(0, "end")
            else:
                self._set_status(self._login_status, r.text, err=True)
        except Exception as e:
            self._set_status(self._login_status, str(e), err=True)

    # ═══════════════════════════════════════════
    #   MASS INVITER
    # ═══════════════════════════════════════════
    def show_inviter(self):
        sf = self._scroll_frame()
        self._page_title(sf, "Inject a username list into your target group or channel.")

        self._inv_acc_vars = {}
        self._account_picker(sf, self._inv_acc_vars)

        cfg = self._section(sf, "TARGET & SETTINGS")
        self._inv_group = self._field(cfg, "Target Group / Channel", "@username or link")
        self._inv_chk_ch = self._chk(cfg, "Target is a Broadcast Channel", default=False, pady=(16, 0))
        self._inv_delay  = self._field(cfg, "Delay (seconds)", "15", default="15")
        self._pad(cfg, 20)

        txt_card = self._section(sf, "USERNAME LIST (one per line)")
        self._inv_textbox = ctk.CTkTextbox(
            txt_card, height=180, font=("Courier", 13), fg_color=C_BG,
            text_color=C_TEXT, border_width=1, border_color=C_BORDER, corner_radius=4
        )
        self._inv_textbox.pack(fill="x", padx=24, pady=24)
        self._inv_textbox.insert("1.0", "@user1\n@user2\n@user3")

        btn_row = ctk.CTkFrame(sf, fg_color="transparent")
        btn_row.pack(fill="x", padx=40, pady=(24, 0))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(btn_row, text="Start Inviting", command=self._start_inviter,
                      font=("Courier", 14, "bold"), fg_color=C_CYAN, hover_color=C_CYAN_HOVER, text_color=C_BG, height=36, corner_radius=4
                      ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Stop All", command=self._stop_inviter,
                      font=("Courier", 14, "bold"), fg_color=C_RED_DIM, hover_color="#3A1010", text_color=C_RED, height=36, corner_radius=4,
                      border_width=1, border_color="#5A1515"
                      ).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self._inv_status = self._status_lbl(sf)
        self._pad(sf, 30)

    def _start_inviter(self):
        if not self.accounts: messagebox.showerror("Error", "No accounts available."); return
        accs = [v.get() for v in self._inv_acc_vars.values() if v.get()]
        if not accs: messagebox.showerror("Error", "No accounts selected."); return
        try:
            r = requests.post(f"{API_BASE}/inviter/invite-by-username", json={
                "accounts": accs, "target_group": self._inv_group.get().strip(),
                "usernames": self._inv_textbox.get("1.0", "end-1c").split(), "delay": float(self._inv_delay.get() or 15)
            })
            self._set_status(self._inv_status, "Inviter started." if r.status_code == 200 else r.text, ok=r.status_code == 200, err=r.status_code != 200)
        except Exception as e:
            self._set_status(self._inv_status, str(e), err=True)

    def _stop_inviter(self):
        try:
            requests.post(f"{API_BASE}/inviter/stop")
            self._set_status(self._inv_status, "Stop signal sent.", ok=True)
        except Exception as e:
            self._set_status(self._inv_status, str(e), err=True)

    # ═══════════════════════════════════════════
    #   JOIN GROUP
    # ═══════════════════════════════════════════
    def show_join(self):
        sf = self._scroll_frame()
        self._page_title(sf, "Force all connected accounts to join a target group.")
        card = self._section(sf, "TARGET GROUP")
        self._join_entry = self._field(card, "Group / Channel", "@groupname  or  invite link")
        self._pad(card, 8)
        ctk.CTkButton(
            card, text="Join Group With All Accounts", command=self._start_join,
            font=("Courier", 14, "bold"), height=36, corner_radius=4,
            fg_color=C_CYAN, hover_color=C_CYAN_HOVER, text_color=C_BG
        ).pack(fill="x", padx=24, pady=(10, 24))
        self._join_status = self._status_lbl(sf)

    def _start_join(self):
        if not self.accounts: return
        try:
            r = requests.post(f"{API_BASE}/join-group", json={"accounts": self.accounts, "target_group": self._join_entry.get().strip(), "delay": 15})
            self._set_status(self._join_status, "Join started." if r.status_code == 200 else r.text, ok=r.status_code == 200, err=r.status_code != 200)
        except Exception as e:
            self._set_status(self._join_status, str(e), err=True)

    # ═══════════════════════════════════════════
    #   DATA SCRAPER
    # ═══════════════════════════════════════════
    def show_scraper(self):
        sf = self._scroll_frame()
        self._page_title(sf, "Extract members from any Telegram group or channel.")

        src = self._section(sf, "SOURCE GROUP")
        self._scrape_entry = self._field(src, "Group / Channel", "@groupname")
        self._pad(src, 20)

        flt = self._section(sf, "FILTERS")
        self._pad(flt, 12)
        self._flt_usr  = self._chk(flt, "Users with @usernames only  (recommended)", pady=(0,8))
        self._flt_bot  = self._chk(flt, "Filter out bots", pady=(0,8))
        self._flt_act  = self._chk(flt, "Active recently only", default=False, pady=(0,8))
        self._flt_ph   = self._chk(flt, "Must have phone number", default=False, pady=(0,8))
        self._pad(flt, 12)

        self._btn_primary(sf, "Start Scraping", self._start_scrape, pady=(24, 0))
        self._scrape_status = self._status_lbl(sf)

        self._export_row = ctk.CTkFrame(sf, fg_color="transparent")
        ex = ctk.CTkFrame(self._export_row, fg_color="transparent")
        ex.pack(fill="x", padx=40, pady=8)
        ex.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(ex, text="Export CSV", command=self._export_csv, font=("Courier", 14, "bold"), height=32, fg_color=C_SURFACE, hover_color=C_SURFACE2, text_color=C_TEXT, corner_radius=4, border_width=1, border_color=C_BORDER).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(ex, text="Export TXT", command=self._export_txt, font=("Courier", 14, "bold"), height=32, fg_color=C_SURFACE, hover_color=C_SURFACE2, text_color=C_TEXT, corner_radius=4, border_width=1, border_color=C_BORDER).grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self._pad(sf, 30)

    def _start_scrape(self):
        if not self.accounts: messagebox.showerror("Error", "No accounts."); return
        grp = self._scrape_entry.get().strip()
        if not grp: return
        self._set_status(self._scrape_status, "Scraping — please wait…")
        self._export_row.pack_forget()

        def task():
            try:
                r = requests.post(f"{API_BASE}/scraper/scrape", json={
                    "account": self.accounts[0], "group_url": grp,
                    "filter_has_username": self._flt_usr.get(), "filter_no_bots": self._flt_bot.get(),
                    "filter_has_phone": self._flt_ph.get(), "filter_active_recently": self._flt_act.get(),
                    "filter_inactive": False, "filter_has_name": False
                })
                if r.status_code == 200:
                    d = r.json(); self.scrape_cache_id = d.get("cache_id"); cnt = d.get("count", 0)
                    self.after(0, lambda: self._set_status(self._scrape_status, f"Extracted {cnt} members.", ok=True))
                    self.after(0, lambda: self._export_row.pack(fill="x"))
                else:
                    self.after(0, lambda: self._set_status(self._scrape_status, r.text, err=True))
            except Exception as e:
                self.after(0, lambda: self._set_status(self._scrape_status, str(e), err=True))
        threading.Thread(target=task, daemon=True).start()

    def _export_csv(self):
        if not self.scrape_cache_id: return
        try:
            r = requests.get(f"{API_BASE}/scraper/export/{self.scrape_cache_id}")
            if r.status_code == 200:
                p = filedialog.asksaveasfilename(parent=self, defaultextension=".csv", filetypes=[("CSV", "*.csv")])
                if p: open(p, "wb").write(r.content); self._set_status(self._scrape_status, f"Saved: {p}", ok=True)
        except Exception as e: self._set_status(self._scrape_status, str(e), err=True)

    def _export_txt(self):
        if not self.scrape_cache_id: return
        try:
            r = requests.get(f"{API_BASE}/scraper/export-txt/{self.scrape_cache_id}")
            if r.status_code == 200:
                p = filedialog.asksaveasfilename(parent=self, defaultextension=".txt", filetypes=[("Text", "*.txt")])
                if p: open(p, "wb").write(r.content); self._set_status(self._scrape_status, f"Saved: {p}", ok=True)
        except Exception as e: self._set_status(self._scrape_status, str(e), err=True)

    # ═══════════════════════════════════════════
    #   GROUP TO GROUP
    # ═══════════════════════════════════════════
    def show_group_inviter(self):
        sf = self._scroll_frame()
        self._page_title(sf, "Scrape members from a source group and inject them into a target.")

        self._g2g_acc_vars = {}
        self._account_picker(sf, self._g2g_acc_vars)

        cfg = self._section(sf, "SOURCE  →  TARGET")
        self._g2g_src   = self._field(cfg, "Source Group (scrape from)", "@source")
        self._g2g_tgt   = self._field(cfg, "Target Group (inject into)", "@target")
        self._g2g_ch    = self._chk(cfg, "Target is a Broadcast Channel", default=False, pady=(16, 0))
        self._g2g_delay = self._field(cfg, "Delay (seconds)", "15", default="15")
        self._pad(cfg, 20)

        btn_row = ctk.CTkFrame(sf, fg_color="transparent")
        btn_row.pack(fill="x", padx=40, pady=(24, 0))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(btn_row, text="Start Transfer", command=self._start_g2g, font=("Courier", 14, "bold"), fg_color=C_CYAN, hover_color=C_CYAN_HOVER, text_color=C_BG, height=36, corner_radius=4).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Stop", command=self._stop_inviter, font=("Courier", 14, "bold"), fg_color=C_RED_DIM, hover_color="#3A1010", text_color=C_RED, height=36, corner_radius=4, border_width=1, border_color="#5A1515").grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self._g2g_status = self._status_lbl(sf)
        self._pad(sf, 30)

    def _start_g2g(self):
        if not self.accounts: messagebox.showerror("Error", "No accounts."); return
        accs = [v.get() for v in self._g2g_acc_vars.values() if v.get()]
        if not accs: messagebox.showerror("Error", "No accounts selected."); return
        src = self._g2g_src.get().strip()
        tgt = self._g2g_tgt.get().strip()
        if not src or not tgt: return
        try:
            r = requests.post(f"{API_BASE}/inviter/invite-group", json={
                "accounts": accs, "primary_account": accs[0], "source_group": src, "target_group": tgt, "delay": float(self._g2g_delay.get() or 15)
            })
            self._set_status(self._g2g_status, "Transfer started." if r.status_code == 200 else r.text, ok=r.status_code == 200, err=r.status_code != 200)
        except Exception as e:
            self._set_status(self._g2g_status, str(e), err=True)

    # ═══════════════════════════════════════════
    #   ACCOUNT WARMUP
    # ═══════════════════════════════════════════
    def show_warmup(self):
        sf = self._scroll_frame()
        self._page_title(sf, "Simulate natural human activity to prevent Telegram bans.")

        info_card = self._section(sf, "WARMUP PARAMETERS")
        params = [
            ("Reactions per group",  "3"),
            ("Messages to send",     "3"),
            ("Reaction delay",       "10 s"),
            ("Chat delay",           "20 s"),
            ("Accounts connected",   f"{len(self.accounts)}"),
        ]
        self._pad(info_card, 8)
        for label, val in params:
            row = ctk.CTkFrame(info_card, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=8)
            ctk.CTkLabel(row, text=label, font=("Courier", 14), text_color=C_TEXT2, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=("Courier", 14, "bold"), text_color=C_CYAN, anchor="e").pack(side="right")
        self._pad(info_card, 16)

        self._warmup_status = self._status_lbl(sf)
        self._btn_primary(sf, "Start Warmup  —  All Accounts", self._start_warmup, pady=(16, 20))

    def _start_warmup(self):
        if not self.accounts: return
        try:
            r = requests.post(f"{API_BASE}/warm/start", json={
                "accounts": self.accounts, "do_react": True, "do_chat": True,
                "reactions_per_group": 3, "messages_to_send": 3, "react_delay": 10.0, "chat_delay": 20.0
            })
            self._set_status(self._warmup_status, "Warmup started." if r.status_code == 200 else r.text, ok=r.status_code == 200, err=r.status_code != 200)
        except Exception as e:
            self._set_status(self._warmup_status, str(e), err=True)

    # ═══════════════════════════════════════════
    #   BOT STARTER
    # ═══════════════════════════════════════════
    def show_bot_starter(self):
        sf = self._scroll_frame()
        self._page_title(sf, "Mass-send /start to any Telegram bot from all accounts.")

        card = self._section(sf, "CONFIGURATION")
        self._bot_entry   = self._field(card, "Bot Username", "@my_bot")
        self._bot_dmin    = self._field(card, "Min Delay (seconds)", "1", default="1")
        self._bot_dmax    = self._field(card, "Max Delay (seconds)", "3", default="3")
        self._pad(card, 20)

        self._bot_status = self._status_lbl(sf)
        self._btn_primary(sf, "Send /start to All Accounts", self._start_bot, pady=(16, 20))

    def _start_bot(self):
        if not self.accounts: messagebox.showwarning("Error", "No accounts."); return
        tgt = self._bot_entry.get().strip()
        if not tgt: messagebox.showwarning("Error", "Enter a bot username."); return
        try:
            r = requests.post(f"{API_BASE}/bot/start", json={
                "accounts": self.accounts, "bot_username": tgt,
                "delay_min": int(self._bot_dmin.get() or 1), "delay_max": int(self._bot_dmax.get() or 3)
            }).json()
            self._set_status(self._bot_status, r.get("message", "Bot clicker started."), ok=True)
        except Exception as e:
            self._set_status(self._bot_status, str(e), err=True)

    # ═══════════════════════════════════════════
    #   UPDATER
    # ═══════════════════════════════════════════
    def show_updater(self):
        sf = self._scroll_frame()
        self._page_title(sf, "Update the tool to get the newest features.")

        card = self._section(sf, "SOFTWARE UPDATE")
        ctk.CTkLabel(card, text="Click the button below to download the latest features and bug fixes.", font=("Courier", 14), text_color=C_TEXT2).pack(padx=24, pady=(20, 10), anchor="w")

        self._update_status = self._status_lbl(sf)
        self._btn_primary(sf, "Check & Update", self._run_update, pady=(20, 20))

    def _run_update(self):
        self._set_status(self._update_status, "Pulling latest changes...", ok=False)
        self.update()
        try:
            result = subprocess.run(["git", "pull"], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
            if result.returncode == 0:
                if "Already up to date." in result.stdout:
                    self._set_status(self._update_status, "You are already on the latest version!", ok=True)
                else:
                    self._set_status(self._update_status, "Update successful! Please restart the application.", ok=True)
                    messagebox.showinfo("Update Complete", "The tool has been updated successfully. Please close and restart the application.")
            else:
                self._set_status(self._update_status, f"Update failed: {result.stderr}", err=True)
        except Exception as e:
            self._set_status(self._update_status, f"Error: {e}", err=True)

    # ═══════════════════════════════════════════
    #   MEDIA DOWNLOADER
    # ═══════════════════════════════════════════
    def show_media_downloader(self):
        sf = self._scroll_frame()
        self._page_title(sf, "Bulk download videos from any public or private group/channel.")

        card = self._section(sf, "CONFIGURATION")

        ctk.CTkLabel(card, text="Account", font=("Courier", 12, "bold"), text_color=C_TEXT2, anchor="w").pack(anchor="w", padx=24, pady=(20, 6))
        self._dl_acc_var = ctk.StringVar(value="Select account")
        ctk.CTkOptionMenu(
            card, values=self.accounts if self.accounts else ["No accounts"], variable=self._dl_acc_var,
            font=("Courier", 14), height=32, corner_radius=4,
            fg_color=C_BG, button_color=C_CYAN, button_hover_color=C_CYAN_HOVER, text_color=C_TEXT,
            dropdown_fg_color=C_SURFACE, dropdown_hover_color=C_SURFACE2, dropdown_text_color=C_TEXT
        ).pack(fill="x", padx=24, pady=(0, 0))

        self._dl_target = self._field(card, "Group / Channel", "https://t.me/…  or  @channel")
        self._dl_limit  = self._field(card, "Messages to scan back", "100", default="100")

        ctk.CTkLabel(card, text="Save Folder", font=("Courier", 12, "bold"), text_color=C_TEXT2, anchor="w").pack(anchor="w", padx=24, pady=(18, 6))

        self._dl_folder = ""
        folder_row = ctk.CTkFrame(card, fg_color="transparent")
        folder_row.pack(fill="x", padx=24, pady=(0, 24))
        folder_row.grid_columnconfigure(0, weight=1)

        self._dl_folder_lbl = ctk.CTkLabel(folder_row, text="Default downloads folder", font=("Courier", 14), text_color=C_TEXT3, anchor="w")
        self._dl_folder_lbl.grid(row=0, column=0, sticky="ew")

        def _pick():
            d = filedialog.askdirectory(parent=self)
            if d: self._dl_folder = d; self._dl_folder_lbl.configure(text=d, text_color=C_TEXT)

        ctk.CTkButton(
            folder_row, text="Browse", command=_pick, font=("Courier", 12, "bold"), width=90, height=40, corner_radius=4,
            fg_color=C_SURFACE2, hover_color=C_BORDER, text_color=C_TEXT, border_width=1, border_color=C_BORDER
        ).grid(row=0, column=1, padx=(12, 0))

        self._dl_status = self._status_lbl(sf)
        self._btn_primary(sf, "Start Downloader", self._start_dl, pady=(16, 20))

    def _start_dl(self):
        acc = self._dl_acc_var.get()
        if acc in ("Select account", "No accounts"): messagebox.showwarning("Error", "Select a valid account."); return
        tgt = self._dl_target.get().strip()
        if not tgt: messagebox.showwarning("Error", "Enter a target."); return
        self._set_status(self._dl_status, "Sending to server…", ok=True)
        def run():
            try:
                r = requests.post(f"{API_BASE}/media/download", json={
                    "account": acc, "target_chat": tgt, "limit": int(self._dl_limit.get() or 100), "save_path": self._dl_folder
                }).json()
                self.after(0, lambda: self._set_status(self._dl_status, r.get("message", "Downloader started — see Terminal Logs."), ok=True))
            except Exception as e:
                self.after(0, lambda: self._set_status(self._dl_status, str(e), err=True))
        threading.Thread(target=run, daemon=True).start()

    # ═══════════════════════════════════════════
    #   AUTO VIDEO POSTER
    # ═══════════════════════════════════════════
    def show_video_poster(self):
        sf = self._scroll_frame()
        self._page_title(sf, "Automatically upload videos from a folder to groups/channels.")

        self._vp_acc_vars = {}
        self._account_picker(sf, self._vp_acc_vars)

        card = self._section(sf, "POSTING SETTINGS")
        
        self._vp_target = self._field(card, "Target Group / Channel", "https://t.me/…  or  @channel")
        self._vp_delay  = self._field(card, "Delay between videos (seconds)", "15", default="15")

        ctk.CTkLabel(card, text="Video Folder", font=("Courier", 12, "bold"), text_color=C_TEXT2, anchor="w").pack(anchor="w", padx=24, pady=(18, 6))

        self._vp_folder = ""
        folder_row = ctk.CTkFrame(card, fg_color="transparent")
        folder_row.pack(fill="x", padx=24, pady=(0, 24))
        folder_row.grid_columnconfigure(0, weight=1)

        self._vp_folder_lbl = ctk.CTkLabel(folder_row, text="Select folder containing videos", font=("Courier", 14), text_color=C_TEXT3, anchor="w")
        self._vp_folder_lbl.grid(row=0, column=0, sticky="ew")

        def _pick():
            d = filedialog.askdirectory(parent=self)
            if d: self._vp_folder = d; self._vp_folder_lbl.configure(text=d, text_color=C_TEXT)

        ctk.CTkButton(
            folder_row, text="Browse", command=_pick, font=("Courier", 12, "bold"), width=90, height=40, corner_radius=4,
            fg_color=C_SURFACE2, hover_color=C_BORDER, text_color=C_TEXT, border_width=1, border_color=C_BORDER
        ).grid(row=0, column=1, padx=(12, 0))

        btn_row = ctk.CTkFrame(sf, fg_color="transparent")
        btn_row.pack(fill="x", padx=40, pady=(24, 0))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(btn_row, text="Start Auto Poster", command=self._start_video_poster, font=("Courier", 14, "bold"), fg_color=C_CYAN, hover_color=C_CYAN_HOVER, text_color=C_BG, height=36, corner_radius=4).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Stop", command=self._stop_video_poster, font=("Courier", 14, "bold"), fg_color=C_RED_DIM, hover_color="#3A1010", text_color=C_RED, height=36, corner_radius=4, border_width=1, border_color="#5A1515").grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self._vp_status = self._status_lbl(sf)
        self._pad(sf, 30)

    def _start_video_poster(self):
        if not self.accounts: messagebox.showerror("Error", "No accounts."); return
        accs = [v.get() for v in self._vp_acc_vars.values() if v.get()]
        if not accs: messagebox.showerror("Error", "No accounts selected."); return
        tgt = self._vp_target.get().strip()
        if not tgt: messagebox.showwarning("Error", "Enter a target."); return
        if not self._vp_folder: messagebox.showwarning("Error", "Select a video folder."); return
        
        self._set_status(self._vp_status, "Starting Auto Poster...", ok=True)
        def run():
            try:
                r = requests.post(f"{API_BASE}/media/auto-post", json={
                    "accounts": accs, "target_chat": tgt, 
                    "folder_path": self._vp_folder, "delay_sec": int(self._vp_delay.get() or 15)
                }).json()
                self.after(0, lambda: self._set_status(self._vp_status, r.get("message", "Started."), ok=True))
            except Exception as e:
                self.after(0, lambda: self._set_status(self._vp_status, str(e), err=True))
        threading.Thread(target=run, daemon=True).start()
        
    def _stop_video_poster(self):
        try:
            requests.post(f"{API_BASE}/media/auto-post/stop")
            self._set_status(self._vp_status, "Stop signal sent.", err=True)
        except Exception as e:
            self._set_status(self._vp_status, f"Error: {e}", err=True)

    # ═══════════════════════════════════════════
    #   PROMOTE TO ADMIN
    # ═══════════════════════════════════════════
    def show_promote_admin(self):
        sf = self._scroll_frame()
        self._page_title(sf, "Promote your normal saved accounts to Admin using an existing Admin account.")

        card1 = self._section(sf, "1. SELECT THE MASTER ADMIN")
        ctk.CTkLabel(card1, text="Admin Account", font=("Courier", 12, "bold"), text_color=C_TEXT2, anchor="w").pack(anchor="w", padx=24, pady=(16, 6))
        self._pa_admin_var = ctk.StringVar(value="Select account")
        ctk.CTkOptionMenu(
            card1, values=self.accounts if self.accounts else ["No accounts"], variable=self._pa_admin_var,
            font=("Courier", 14), height=32, corner_radius=4,
            fg_color=C_BG, button_color=C_CYAN, button_hover_color=C_CYAN_HOVER, text_color=C_TEXT,
            dropdown_fg_color=C_SURFACE, dropdown_hover_color=C_SURFACE2, dropdown_text_color=C_TEXT
        ).pack(fill="x", padx=24, pady=(0, 20))

        self._pa_target = self._field(card1, "Target Group / Channel", "https://t.me/…  or  @group")
        
        self._pa_acc_vars = {}
        self._account_picker(sf, self._pa_acc_vars, label="2. SELECT ACCOUNTS TO PROMOTE")

        self._pa_status = self._status_lbl(sf)
        self._btn_primary(sf, "Promote Selected Accounts", self._start_promote_admin, pady=(16, 20))

    def _start_promote_admin(self):
        admin = self._pa_admin_var.get()
        if admin in ("Select account", "No accounts"): messagebox.showwarning("Error", "Select the Admin account."); return
        tgt = self._pa_target.get().strip()
        if not tgt: messagebox.showwarning("Error", "Enter the target group."); return
        
        accs = [v.get() for v in self._pa_acc_vars.values() if v.get()]
        if not accs: messagebox.showerror("Error", "Select at least one account to promote."); return
        
        if admin in accs: messagebox.showwarning("Warning", f"The admin account {admin} is also selected to be promoted. Continuing anyway.");
        
        self._set_status(self._pa_status, "Sending to server...", ok=True)
        def run():
            try:
                r = requests.post(f"{API_BASE}/group/promote", json={
                    "admin_account": admin, "target_chat": tgt, 
                    "accounts_to_promote": accs, "delay_sec": 2
                }).json()
                self.after(0, lambda: self._set_status(self._pa_status, r.get("message", "Started."), ok=True))
            except Exception as e:
                self.after(0, lambda: self._set_status(self._pa_status, str(e), err=True))
        threading.Thread(target=run, daemon=True).start()

    # ═══════════════════════════════════════════
    #   TERMINAL LOGS
    # ═══════════════════════════════════════════
    def show_terminal(self):
        outer = ctk.CTkFrame(self.content, fg_color=C_BG, corner_radius=4)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(outer, fg_color="transparent", height=70)
        hdr.grid(row=0, column=0, sticky="ew", padx=40, pady=(24, 0))
        hdr.grid_propagate(False)

        ctk.CTkLabel(hdr, text="Terminal Logs", font=("Courier", 18, "bold"), text_color=C_TEXT, anchor="w").pack(side="left", anchor="w")

        btn_area = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_area.pack(side="right", anchor="e")

        ctk.CTkButton(btn_area, text="Clear Tab", command=self._clear_logs, font=("Courier", 13, "bold"), width=100, height=40, corner_radius=4, fg_color=C_RED_DIM, hover_color="#3A1010", text_color=C_RED, border_width=1, border_color="#5A1515").pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_area, text="Save Logs", command=self._save_logs, font=("Courier", 13, "bold"), width=110, height=40, corner_radius=4, fg_color=C_SURFACE, hover_color=C_SURFACE2, text_color=C_TEXT2, border_width=1, border_color=C_BORDER).pack(side="left")

        self._log_tabs = ctk.CTkTabview(outer, fg_color=C_SURFACE, segmented_button_fg_color=C_BG, segmented_button_selected_color=C_CYAN_DIM, segmented_button_selected_hover_color=C_CYAN, text_color=C_TEXT)
        self._log_tabs.grid(row=1, column=0, sticky="nsew", padx=40, pady=20)
        self._log_boxes = {} # task_name -> CTkTextbox

        self._fetch_logs()

    def _fetch_logs(self):
        if not self.is_terminal_active: return
        try:
            r = requests.get(f"{API_BASE}/logs", timeout=2)
            if r.status_code == 200:
                logs_dict = r.json().get("logs", {})
                for task_name, logs in logs_dict.items():
                    if task_name not in self._log_boxes:
                        self._log_tabs.add(task_name)
                        tb = ctk.CTkTextbox(self._log_tabs.tab(task_name), font=("Courier", 13), fg_color="transparent", text_color=C_CYAN, border_width=0, wrap="word")
                        tb.pack(fill="both", expand=True, padx=12, pady=12)
                        self._log_boxes[task_name] = tb
                    
                    new_text = "\n".join(logs)
                    if self._log_boxes[task_name].get("1.0", "end-1c") != new_text:
                        self._log_boxes[task_name].delete("1.0", "end")
                        self._log_boxes[task_name].insert("1.0", new_text)
                        self._log_boxes[task_name].yview("end")
        except Exception: pass
        self.after(2000, self._fetch_logs)

    def _clear_logs(self):
        try:
            current_tab = self._log_tabs.get()
            if not current_tab: return
            requests.post(f"{API_BASE}/logs/clear", json={"task": current_tab})
            if current_tab in self._log_boxes:
                self._log_boxes[current_tab].delete("1.0", "end")
        except Exception as e: messagebox.showerror("Error", str(e))

    def _save_logs(self):
        try:
            current_tab = self._log_tabs.get()
            if not current_tab or current_tab not in self._log_boxes: return
            text = self._log_boxes[current_tab].get("1.0", "end-1c")
            if not text.strip(): messagebox.showinfo("Empty", "No logs to save."); return
            p = filedialog.asksaveasfilename(parent=self, defaultextension=".txt", initialfile=f"{current_tab}_logs.txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
            if p:
                open(p, "w", encoding="utf-8").write(text); messagebox.showinfo("Saved", f"Logs saved to:\n{p}")
        except Exception as e: messagebox.showerror("Error", str(e))

def run_server():
    import sys, os
    if sys.stdout is None: sys.stdout = open(os.devnull, "w")
    if sys.stderr is None: sys.stderr = open(os.devnull, "w")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(1.5)
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    App().mainloop()
