import os
import re

directory = '/Users/bongrun/Documents/Tool_Adder'

device_params = """,
        device_model="iPhone 13 Pro Max",
        system_version="15.5",
        app_version="8.7.1",
        lang_code="en",
        system_lang_code="en"
    )"""

for filename in os.listdir(directory):
    if filename.endswith(".py") and filename != "fix_telethon.py":
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as f:
            content = f.read()
        
        # We look for something like: TelegramClient(session_path, API_ID, API_HASH)
        # And make sure it doesn't already have device_model
        if "device_model=" not in content and "TelegramClient" in content:
            # Replace TelegramClient(..., API_ID, API_HASH)
            # Regex to match TelegramClient( <arg1>, <arg2>, <arg3> )
            new_content = re.sub(
                r'(TelegramClient\s*\([^,]+,\s*[A-Za-z0-9_]+,\s*[A-Za-z0-9_]+\s*)\)',
                r'\1' + device_params,
                content
            )
            
            # Additional check for randomizing delay
            if "asyncio.sleep(delay)" in new_content:
                new_content = new_content.replace(
                    "await asyncio.sleep(delay)",
                    "await asyncio.sleep(delay * __import__('random').uniform(0.8, 1.5))"
                )

            if new_content != content:
                with open(filepath, 'w') as f:
                    f.write(new_content)
                print(f"Updated {filename} with anti-ban measures.")
