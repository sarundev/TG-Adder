import os
import sys
import time
import random
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
import questionary
from rich.style import Style
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
import urllib.request
import json
import uuid
import hashlib
import platform
import runpy

console = Console()

# --- PyInstaller Subprocess Hack ---
# When frozen, sys.executable is the compiled binary. We intercept calls to run sub-scripts.
if getattr(sys, 'frozen', False) and len(sys.argv) > 1 and sys.argv[1].endswith('.py'):
    script_to_run = sys.argv[1]
    # We must run it natively in the same memory space since we don't have a python.exe
    sys.argv = [script_to_run] # Mask arguments for the subscript
    runpy.run_path(script_to_run, run_name="__main__")
    sys.exit(0)

SERVER_URL = "https://web-production-c4d18.up.railway.app" # Pointing to live Railway server

def get_base_path():
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return base_path

def get_hwid():
    """Generates a unique hardware ID for this device."""
    system_info = f"{platform.node()}-{uuid.getnode()}-{platform.machine()}"
    return hashlib.sha256(system_info.encode()).hexdigest()[:16]

def verify_license():
    """Checks local license or prompts for one and verifies with the server."""
    license_file = ".license_token"
    token = None
    
    if os.path.exists(license_file):
        with open(license_file, "r") as f:
            token = f.read().strip()
            
    if not token:
        os.system("cls" if os.name == "nt" else "clear")
        console.print("[bold cyan]=== SOFTWARE ACTIVATION ===[/bold cyan]")
        console.print("[cyan]This tool is locked to your specific device hardware.[/cyan]\n")
        token = input("Enter your License Token: ").strip()
        if not token:
            sys.exit(1)
            
    hwid = get_hwid()
    
    console.print("\n[bold yellow]Authenticating with licensing server...[/bold yellow]")
    try:
        data = json.dumps({"token": token, "hwid": hwid}).encode('utf-8')
        req = urllib.request.Request(f"{SERVER_URL}/api/license/verify", data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode())
            if res.get("status") == "success":
                console.print("[bold green]Activation Successful! Access Granted.[/bold green]")
                with open(license_file, "w") as f:
                    f.write(token)
                time.sleep(1)
                return True
    except urllib.error.HTTPError as e:
        if e.code == 401:
            console.print("[bold red]ERROR: Invalid or Hardware-Bound Token![/bold red]")
            console.print("[red]This token is either incorrect or already bound to another computer.[/red]")
        else:
            console.print(f"[bold red]Server Error: {e.code}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Could not connect to licensing server: {e}[/bold red]")
        console.print("[yellow]Make sure your API server (server.py) is running on Railway or locally.[/yellow]")
        
    if os.path.exists(license_file):
        os.remove(license_file) # Remove invalid token
    input("\nPress Enter to exit...")
    sys.exit(1)

# Define paths to scripts
SCRIPTS = {
    "Login to Telegram Account": "telegram_login.py",
    "Check Account Health": "check_account_health.py",
    "Clean & Organize Accounts": "clean_accounts.py",
    "Remove All Accounts": "remove_all_accounts.py",
    "Export Contacts": "get_contact.py",
    
    "Scrape Public Group Members": "scrape_member_public_group.py",
    "Scrape Private Group Members": "scrape_member_private_group.py",
    "Scrape and Add Members": "scrape_and_add.py",
    
    "Add User to Group": "add_user_to_group.py",
    "Add User to Channel": "add_user_to_channel.py",
    "Add Member to Channel": "add_member_to_channel.py",
    
    "Auto Join Group": "auto_join_group.py",
    "Auto Forward & Replace Links": "auto_forward_and_replace.py",
    "Auto Send Message to Group": "auto_send_message_to_group.py",
    "Auto Warm Account": "auto_warm_account.py",
    
    "Start API Server": "server.py",
    "Exit": None
}

def boot_sequence():
    """Simulates a hacker terminal boot sequence."""
    os.system("cls" if os.name == "nt" else "clear")
    console.print("[bold green]INITIATING BOOT SEQUENCE...[/bold green]\n")
    time.sleep(0.5)
    
    steps = [
        "Establishing secure connection to mainframe...",
        "Bypassing proxy firewalls [██████████░░░░░░░░]",
        "Decrypting payload modules...",
        "Injecting rootkit into memory...",
        "Masking IP address...",
        "Access GRANTED."
    ]
    
    for step in steps:
        delay = random.uniform(0.1, 0.4)
        time.sleep(delay)
        if "GRANTED" in step:
            console.print(f"[bold cyan blink]> {step}[/bold cyan blink]")
            time.sleep(0.8)
        else:
            console.print(f"[green]> {step}[/green]")
            
    os.system("cls" if os.name == "nt" else "clear")

def print_header():
    os.system("cls" if os.name == "nt" else "clear")
    
    ascii_art = """
 ████████╗ ██████╗      ██████╗  ██████╗ ██████╗ ██████╗ 
 ╚══██╔══╝██╔════╝     ██╔════╝ ██╔═══██╗██╔══██╗██╔══██╗
    ██║   ██║  ███╗    ██║  ███╗██║   ██║██║  ██║██║  ██║
    ██║   ██║   ██║    ██║   ██║██║   ██║██║  ██║██║  ██║
    ██║   ╚██████╔╝    ╚██████╔╝╚██████╔╝██████╔╝██████╔╝
    ╚═╝    ╚═════╝      ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝ 
    """
    title = Text(ascii_art, style="bold bright_green")
    
    subtitle = Text(
        "ROOT@TELEGRAM_SUITE:~$ systemctl status tools\n"
        "[+] SYSTEM: ONLINE    [+] ENCRYPTION: AES-256    [+] STEALTH: ACTIVE", 
        style="bold cyan"
    )
    
    panel = Panel(
        Align.center(title + "\n" + subtitle),
        border_style="bright_green",
        padding=(0, 2)
    )
    console.print(panel)
    console.print()

def main_menu():
    boot_sequence()
    while True:
        print_header()
        
        choices = [
            questionary.Separator("\n [ ERROR: MODULES NOT FOUND ] " if False else "\n=== [ CORE_IDENTITY ] ==="),
            "Login to Telegram Account",
            "Check Account Health",
            "Clean & Organize Accounts",
            "Remove All Accounts",
            "Export Contacts",
            
            questionary.Separator("\n=== [ DATA_EXTRACTION ] ==="),
            "Scrape Public Group Members",
            "Scrape Private Group Members",
            "Scrape and Add Members",
            
            questionary.Separator("\n=== [ INFILTRATION ] ==="),
            "Add User to Group",
            "Add User to Channel",
            "Add Member to Channel",
            
            questionary.Separator("\n=== [ AUTOBOTS ] ==="),
            "Auto Join Group",
            "Auto Forward & Replace Links",
            "Auto Send Message to Group",
            "Auto Warm Account",
            
            questionary.Separator("\n=== [ BACKDOOR_SERVER ] ==="),
            "Start API Server",
            questionary.Separator(),
            "Exit"
        ]

        action = questionary.select(
            "root@suite:~# select_payload",
            choices=choices,
            style=questionary.Style([
                ('qmark', 'fg:cyan bold'),
                ('question', 'fg:green bold'),
                ('answer', 'fg:white bold'),
                ('pointer', 'fg:cyan bold'),
                ('highlighted', 'fg:white bold bg:black'),
                ('selected', 'fg:white'),
                ('separator', 'fg:cyan bold'),
                ('instruction', 'fg:darkgray'),
                ('text', 'fg:green')
            ]),
            pointer="█►"
        ).ask()

        if action == "Exit" or action is None:
            console.print("\n[bold yellow]Terminating connection... WIPING LOGS...[/bold yellow]")
            time.sleep(1)
            console.print("[bold yellow]SYSTEM HALTED.[/bold yellow]")
            break
            
        script_file = SCRIPTS.get(action)
        if script_file:
            script_path = os.path.join(get_base_path(), script_file)
            if not os.path.exists(script_path):
                console.print(f"[bold yellow]FATAL: '{script_file}' corrupted or missing![/bold yellow]")
                time.sleep(2)
                continue
                
            console.print(f"\n[bold green]root@suite:~# ./exec {script_file}[/bold green]\n")
            try:
                # If frozen, sys.executable calls our own binary, which intercepts the .py argument at the top!
                subprocess.run([sys.executable, script_path])
            except KeyboardInterrupt:
                console.print("\n[bold yellow][!] PROCESS INTERRUPTED [!][/bold yellow]")
            except Exception as e:
                console.print(f"\n[bold yellow][!] KERNEL PANIC: {e} [!][/bold yellow]")
            
            console.print("\n[bold dark_gray]root@suite:~# press [ENTER] to return to shell...[/bold dark_gray]")
            input()

if __name__ == "__main__":
    verify_license()
    main_menu()
