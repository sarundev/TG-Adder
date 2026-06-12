import os
import glob
import asyncio
import sys
import shutil
from telethon import TelegramClient
from telethon.errors import UserDeactivatedBanError
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import time
import sqlite3

console = Console()

API_ID = 36597503
API_HASH = "ce9a6d0c68789ae5234b77aa081acfac"

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ACCOUNTS_DIR = os.path.join(BASE_DIR, "accounts")
RESTING_DIR = os.path.join(ACCOUNTS_DIR, "resting")
BANNED_DIR = os.path.join(ACCOUNTS_DIR, "banned")

# Ensure directories exist
os.makedirs(RESTING_DIR, exist_ok=True)
os.makedirs(BANNED_DIR, exist_ok=True)

async def clean_accounts():
    os.system("cls" if os.name == "nt" else "clear")
    console.print(Panel("[bold cyan]INITIALIZING ACCOUNT AUTO-CLEANER...[/bold cyan]", border_style="cyan"))
    console.print("[cyan]This tool will automatically move Restricted accounts to the 'resting' folder and Dead accounts to the 'banned' folder.[/cyan]\n")
    
    session_files = glob.glob(os.path.join(ACCOUNTS_DIR, "*.session"))
    if not session_files:
        console.print("[bold red][!] NO ACCOUNTS DETECTED IN MAIN DATABANK.[/bold red]")
        return

    moved_resting = 0
    moved_banned = 0
    healthy = 0
    
    table = Table(title="[bold green]CLEANUP REPORT[/bold green]", box=box.MINIMAL_DOUBLE_HEAD)
    table.add_column("Account Phone", style="cyan", no_wrap=True)
    table.add_column("Action Taken", justify="center")

    for session_path in session_files:
        session_name = os.path.basename(session_path).replace(".session", "")
        client = TelegramClient(session_path, API_ID, API_HASH)
        
        action = None # "banned", "resting", or "healthy"
        reason = ""

        try:
            await client.connect()
            if not await client.is_user_authorized():
                action = "banned"
                reason = "Revoked"
            else:
                me = await client.get_me()
                if me.restricted:
                    action = "resting"
                    reason = "Spam Block"
                else:
                    action = "healthy"
                    reason = "Healthy"
        except UserDeactivatedBanError:
            action = "banned"
            reason = "Deleted by TG"
        except sqlite3.OperationalError as e:
            action = "resting"
            reason = "Locked Database"
        except Exception as e:
            action = "resting"
            reason = "Error"
        finally:
            if client.is_connected():
                try:
                    await client.disconnect()
                except sqlite3.OperationalError:
                    pass

        # Safely move the file AFTER Telethon has fully disconnected and released the SQLite lock
        if action == "banned":
            table.add_row(session_name, f"[bold red]MOVED TO BANNED[/bold red] ({reason})")
            shutil.move(session_path, os.path.join(BANNED_DIR, os.path.basename(session_path)))
            moved_banned += 1
        elif action == "resting":
            table.add_row(session_name, f"[bold yellow]MOVED TO RESTING[/bold yellow] ({reason})")
            shutil.move(session_path, os.path.join(RESTING_DIR, os.path.basename(session_path)))
            moved_resting += 1
        else:
            table.add_row(session_name, f"[bold green]KEPT IN MAIN[/bold green] ({reason})")
            healthy += 1

    console.print(table)
    
    summary_text = f"[bold green]HEALTHY (KEPT):[/bold green] {healthy}    [bold yellow]RESTING (MOVED):[/bold yellow] {moved_resting}    [bold red]BANNED (MOVED):[/bold red] {moved_banned}"
    console.print(Panel(summary_text, title="[bold cyan]CLEANUP SUMMARY[/bold cyan]", border_style="cyan", expand=False))

if __name__ == "__main__":
    asyncio.run(clean_accounts())
