import os
import re

directory = '/Users/bongrun/Documents/Tool_Adder'

for filename in os.listdir(directory):
    if filename.endswith(".py") and filename not in ["fix_rate_limit.py", "fix_telethon.py", "fix_channels.py"]:
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as f:
            content = f.read()

        # Update lists that filter by is_group to also include is_channel
        if "d.is_group]" in content:
            new_content = content.replace(
                "groups = [d for d in dialogs if d.is_group]",
                "groups = [d for d in dialogs if d.is_group or d.is_channel]"
            )
            # Update the print statements that might say "Joined Groups"
            new_content = new_content.replace(
                "print(\"\\n--- Available Joined Groups ---\")",
                "print(\"\\n--- Available Joined Groups & Channels ---\")"
            )
            new_content = new_content.replace(
                "print(\"❌ This Telegram account is not joined to any groups!\")",
                "print(\"❌ This Telegram account is not joined to any groups or channels!\")"
            )
            
            if new_content != content:
                with open(filepath, 'w') as f:
                    f.write(new_content)
                print(f"Updated {filename} to include channels.")
