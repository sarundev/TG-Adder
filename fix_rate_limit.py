import os
import re

directory = '/Users/bongrun/Documents/Tool_Adder'

for filename in os.listdir(directory):
    if filename.endswith(".py") and filename != "fix_rate_limit.py" and filename != "fix_telethon.py":
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as f:
            content = f.read()

        # The pattern looks for the `print(f"   🕒 Waiting {res}s due to rate limit...")` line and the `await asyncio.sleep(res)`
        # We will prepend a check `if res > 120: break`
        
        # We use a regex to capture the indentation level of the `print` statement
        pattern = r'([ \t]+)(print\(f"   🕒 Waiting \{res\}s due to rate limit\.\.\."\)\n[ \t]+await asyncio\.sleep\(res\))'
        
        def replacer(match):
            indent = match.group(1)
            original = match.group(2)
            
            # If the script is told to wait for a rate limit, check if it's too long
            # Skip the account if the wait is greater than 60 seconds (1 minute).
            new_code = (
                f"{indent}if res > 60:\n"
                f"{indent}    print(f\"   ⚠️ Rate limit is too long ({{res}}s)! Skipping this account to save time.\")\n"
                f"{indent}    break\n"
                f"{indent}{original}"
            )
            return new_code
            
        new_content, count = re.subn(pattern, replacer, content)
        
        if count > 0:
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Updated {filename} with rate-limit skip logic.")
