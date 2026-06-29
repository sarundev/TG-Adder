import os
import glob
import sys
from rich.console import Console

console = Console()

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ACCOUNTS_DIR = os.path.join(BASE_DIR, "accounts")
RESTING_DIR = os.path.join(ACCOUNTS_DIR, "resting")
BANNED_DIR = os.path.join(ACCOUNTS_DIR, "banned")

def remove_all_accounts():
    session_files = []
    
    # Collect all .session files from main, resting, and banned directories
    for directory in [ACCOUNTS_DIR, RESTING_DIR, BANNED_DIR]:
        if os.path.exists(directory):
            session_files.extend(glob.glob(os.path.join(directory, "*.session")))

    if not session_files:
        console.print("[bold yellow]No accounts found to remove.[/bold yellow]")
        return

    console.print(f"[bold red]Found {len(session_files)} account(s).[/bold red]")
    confirm = input("Are you sure you want to PERMANENTLY delete all accounts? (y/n): ")
    
    if confirm.lower() == 'y':
        count = 0
        for session_path in session_files:
            try:
                os.remove(session_path)
                console.print(f"[green]Deleted:[/green] {os.path.basename(session_path)}")
                count += 1
            except Exception as e:
                console.print(f"[red]Failed to delete {os.path.basename(session_path)}: {e}[/red]")
        console.print(f"\n[bold green]Successfully deleted {count} accounts.[/bold green]")
    else:
        console.print("[bold yellow]Operation cancelled.[/bold yellow]")

if __name__ == "__main__":
    remove_all_accounts()
