import os
import re

directory = '/Users/bongrun/Documents/Tool_Adder'

replacement_code = """    print("\\nEnter members/text (you can paste multiple lines).")
    print("When you are done, just press ENTER twice (leave a blank line):")
    
    lines = []
    while True:
        try:
            line = input()
            if not line.strip() and not lines:
                continue # ignore leading blank lines
            elif not line.strip():
                break # blank line after content means finish
            lines.append(line)
        except EOFError:
            break
        except KeyboardInterrupt:
            break"""

for filename in os.listdir(directory):
    if filename.endswith(".py") and filename not in ["fix_stdin.py"]:
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as f:
            content = f.read()

        # Check if the file uses sys.stdin for member input
        if "for line in sys.stdin:" in content:
            
            # Use regex to find the block
            pattern = re.compile(
                r'print\("\\nEnter.*?"\)\n\s+print\("\(Press Ctrl\+D.*?"\)\n\s+import sys\n\s+lines = \[\]\n\s+try:\n\s+for line in sys\.stdin:\n\s+lines\.append\(line\)\n\s+except KeyboardInterrupt:\n\s+pass',
                re.DOTALL
            )
            
            new_content = pattern.sub(replacement_code, content)
            
            # Another pattern might not have import sys right there
            pattern2 = re.compile(
                r'print\("\\nEnter.*?"\)\n\s+print\("\(Press Ctrl\+D.*?"\)\n\s+lines = \[\]\n\s+try:\n\s+for line in sys\.stdin:\n\s+lines\.append\(line\)\n\s+except KeyboardInterrupt:\n\s+pass',
                re.DOTALL
            )
            new_content = pattern2.sub(replacement_code, new_content)

            if new_content != content:
                with open(filepath, 'w') as f:
                    f.write(new_content)
                print(f"Fixed stdin in {filename}")
