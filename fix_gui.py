import re

with open('/Users/bongrun/Documents/Tool_Adder/main_gui.py', 'r') as f:
    content = f.read()

# Fix fetch_logs
fetch_logs_old = """    def fetch_logs(self):
        if not self.is_terminal_active: return
        
        try:
            res = requests.get(f"{API_BASE}/logs", timeout=2)
            if res.status_code == 200:
                logs = res.json().get("logs", [])
                
                # Only update if necessary to prevent scrolling jitter
                current_text = self.log_textbox.get("1.0", "end-1c")
                new_text = "\\n".join(logs)
                
                if current_text != new_text:
                    self.log_textbox.delete("1.0", "end")
                    self.log_textbox.insert("1.0", new_text)
                    self.log_textbox.yview("end") # Auto-scroll to bottom
        except:
            pass
            
        # Schedule next update in 2000ms
        self.after(2000, self.fetch_logs)"""

fetch_logs_new = """    def fetch_logs(self):
        if not self.is_terminal_active: return
        
        def task():
            try:
                res = requests.get(f"{API_BASE}/logs", timeout=2)
                if res.status_code == 200:
                    logs = res.json().get("logs", [])
                    new_text = "\\n".join(logs)
                    def update_ui():
                        if not self.is_terminal_active: return
                        current_text = self.log_textbox.get("1.0", "end-1c")
                        if current_text != new_text:
                            self.log_textbox.delete("1.0", "end")
                            self.log_textbox.insert("1.0", new_text)
                            self.log_textbox.yview("end")
                    self.after(0, update_ui)
            except:
                pass
            if self.is_terminal_active:
                self.after(2000, self.fetch_logs)
                
        threading.Thread(target=task, daemon=True).start()"""

content = content.replace(fetch_logs_old, fetch_logs_new)

functions_to_thread = [
    "def load_accounts(self):",
    "def request_code(self):",
    "def verify_code(self):",
    "def start_inviter(self):",
    "def stop_inviter(self):",
    "def start_join(self):",
    "def start_group_inviter(self):",
    "def start_warmup(self):",
]

new_content = content.replace("import threading", "import threading\n\ndef async_thread(func):\n    def wrapper(*args, **kwargs):\n        threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()\n    return wrapper\n")

for func in functions_to_thread:
    new_content = new_content.replace(f"    {func}", f"    @async_thread\n    {func}")

with open('/Users/bongrun/Documents/Tool_Adder/main_gui.py', 'w') as f:
    f.write(new_content)
