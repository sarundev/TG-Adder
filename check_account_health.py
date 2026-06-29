import os
import glob
import asyncio
import sys
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

async def check_health():
    os.system("cls" if os.name == "nt" else "clear")
    console.print(Panel("[bold cyan]INITIALIZING ACCOUNT DIAGNOSTICS...[/bold cyan]", border_style="cyan"))
    
    session_files = glob.glob(os.path.join(ACCOUNTS_DIR, "*.session"))
    if not session_files:
        console.print("[bold red][!] NO ACCOUNTS DETECTED IN DATABANKS.[/bold red]")
        return

    active = 0
    banned = 0
    
    table = Table(title="[bold green]TELEGRAM SUITE : ACCOUNT HEALTH REPORT[/bold green]", box=box.MINIMAL_DOUBLE_HEAD)
    table.add_column("Account Phone", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Details", style="magenta")

    for session_path in session_files:
        session_name = os.path.basename(session_path).replace(".session", "")
        client = TelegramClient(session_path, API_ID, API_HASH)
        
        try:
            await client.connect()
            if not await client.is_user_authorized():
                table.add_row(session_name, "[bold red]REVOKED[/bold red]", "Auth Key Unregistered")
                banned += 1
            else:
                me = await client.get_me()
                if me.restricted:
                    reason = me.restriction_reason[0].text if me.restriction_reason else "Spam Block"
                    table.add_row(session_name, "[bold yellow]RESTRICTED[/bold yellow]", reason)
                    active += 1
                else:
                    table.add_row(session_name, "[bold green]HEALTHY[/bold green]", f"Active as {me.first_name}")
                    active += 1
        except UserDeactivatedBanError:
            table.add_row(session_name, "[bold red]BANNED[/bold red]", "Account Deleted by Telegram")
            banned += 1
        except sqlite3.OperationalError as e:
            table.add_row(session_name, "[bold yellow]LOCKED[/bold yellow]", "Database is in use by another process")
            banned += 1
        except Exception as e:
            table.add_row(session_name, "[bold red]ERROR[/bold red]", str(e))
            banned += 1
        finally:
            try:
                await client.disconnect()
            except sqlite3.OperationalError:
                pass # Ignore if it's locked during disconnect

    console.print(table)
    
    summary_text = f"[bold green]HEALTHY/RESTRICTED:[/bold green] {active}    [bold red]BANNED/DEAD:[/bold red] {banned}"
    console.print(Panel(summary_text, title="[bold cyan]DIAGNOSTIC SUMMARY[/bold cyan]", border_style="cyan", expand=False))

if __name__ == "__main__":
    asyncio.run(check_health())
