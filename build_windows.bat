@echo off
echo Building TELE168 for Windows...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b
)

:: Install dependencies
echo Installing requirements...
pip install -r requirements.txt
pip install pyinstaller

:: Build the application
echo Running PyInstaller...
pyinstaller --noconfirm TELE168.spec

echo.
echo Build complete! You can find your TELE168.exe in the 'dist\TELE168' or 'dist' folder.
pause
