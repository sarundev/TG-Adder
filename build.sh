#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🔧 Patching opentele bug for newer Telethon versions..."
python -c "
import os
import opentele
patch_file = os.path.join(os.path.dirname(opentele.__file__), 'utils.py')
with open(patch_file, 'r') as f:
    content = f.read()
content = content.replace('raise BaseException(\"err\")', 'pass')
with open(patch_file, 'w') as f:
    f.write(content)
"

echo "📦 Installing Node dependencies and building React frontend..."
cd frontend
npm install
npm run build
cd ..

echo "✅ Build complete!"
