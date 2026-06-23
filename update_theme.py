import re

with open("main_gui.py", "r") as f:
    content = f.read()

# Replace tokens
tokens = """# ═══════════════════════════════════════════
#   DESIGN TOKENS  —  Classic Pro
# ═══════════════════════════════════════════
# Based on classic professional IDE/Software UI

C_BG          = "#2B2B2B"   # Classic Dark Grey
C_SIDEBAR     = "#333333"   # Slightly lighter sidebar
C_SURFACE     = "#3C3F41"   # Card surfaces (IntelliJ style)
C_SURFACE2    = "#4C5052"   # Hover/active states
C_BORDER      = "#555555"   # Borders

# Classic Accents
C_CYAN        = "#4A90E2"   # Classic Blue (replacing Cyan)
C_CYAN_DIM    = "#2B4365"   # Faded blue
C_CYAN_HOVER  = "#357ABD"

C_GOLD        = "#F2C94C"   # Standard Yellow/Gold
C_GOLD_DIM    = "#5C4D1D"
C_GOLD_HOVER  = "#D9B444"

C_GREEN       = "#27AE60"
C_GREEN_DIM   = "#164529"

C_RED         = "#EB5757"
C_RED_DIM     = "#5C2626"
C_RED_HOVER   = "#C94A4A"

# Text
C_TEXT        = "#E0E0E0"   # Standard light text
C_TEXT2       = "#A9B7C6"   # Secondary text
C_TEXT3       = "#7A7A7A"   # Dim text"""

content = re.sub(r"# ═══════════════════════════════════════════\n#   DESIGN TOKENS.*?\nC_TEXT3       = \"[^\"]+\"", tokens, content, flags=re.DOTALL)

# Replace corner radius to be classic (sharp/slightly rounded)
content = re.sub(r"corner_radius=\d+", "corner_radius=4", content)
content = re.sub(r"corner_radius=40", "corner_radius=0", content) # For the lock icon ring
content = re.sub(r"corner_radius=36", "corner_radius=0", content)

# Change fonts from Helvetica to standard system font (often just omitted or 'Segoe UI'/'Arial')
# We'll leave Helvetica but reduce the massive sizes
content = re.sub(r'font=\("Helvetica", 36, "bold"\)', 'font=("Helvetica", 24, "bold")', content)
content = re.sub(r'font=\("Helvetica", 24, "bold"\)', 'font=("Helvetica", 18, "bold")', content)
content = re.sub(r'font=\("Helvetica", 28, "bold"\)', 'font=("Helvetica", 20, "bold")', content)

# Change thick heights
content = re.sub(r"height=52", "height=36", content)
content = re.sub(r"height=48", "height=32", content)
content = re.sub(r"height=44", "height=32", content)

with open("main_gui.py", "w") as f:
    f.write(content)

print("Theme updated to Classic!")
