@echo off
REM Windows Build Script for ISI Exams Management System
REM This script helps Windows users who want to build the executable locally

echo ========================================
echo ISI Exams - Windows Build Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from https://python.org
    pause
    exit /b 1
)

echo Python found. Checking version...
python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
if %errorlevel% neq 0 (
    echo ERROR: Python 3.11 or higher is required
    echo Please upgrade your Python installation
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
if exist venv_windows_build rmdir /s /q venv_windows_build
python -m venv venv_windows_build
call venv_windows_build\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install build requirements
echo Installing build dependencies...
if not exist requirements-build.txt (
    echo ERROR: requirements-build.txt not found
    pause
    exit /b 1
)
pip install -r requirements-build.txt

REM Clean previous builds
echo Cleaning previous builds...
if exist build_windows rmdir /s /q build_windows
if exist dist_windows rmdir /s /q dist_windows
if exist ISI_Exams_Windows rmdir /s /q ISI_Exams_Windows

REM Build the executable
echo Building Windows executable...
echo This may take several minutes...
pyinstaller --clean --distpath dist_windows --workpath build_windows isi_exams.spec

REM Check if build was successful
if not exist dist_windows\ISI_Exams (
    echo ERROR: Build failed! Please check the output above.
    pause
    exit /b 1
)

REM Create user-friendly package
echo Creating user-friendly package...
mkdir ISI_Exams_Windows
xcopy /e /i dist_windows\ISI_Exams\* ISI_Exams_Windows\

REM Create launcher script
echo @echo off > ISI_Exams_Windows\Run_ISI_Exams.bat
echo echo Starting ISI Exams Management System... >> ISI_Exams_Windows\Run_ISI_Exams.bat
echo echo. >> ISI_Exams_Windows\Run_ISI_Exams.bat
echo echo Please wait while the application loads... >> ISI_Exams_Windows\Run_ISI_Exams.bat
echo echo Once loaded, your web browser will open automatically. >> ISI_Exams_Windows\Run_ISI_Exams.bat
echo echo. >> ISI_Exams_Windows\Run_ISI_Exams.bat
echo echo If the browser doesn't open automatically, please go to: >> ISI_Exams_Windows\Run_ISI_Exams.bat
echo echo http://localhost:8080/seances.html >> ISI_Exams_Windows\Run_ISI_Exams.bat
echo echo. >> ISI_Exams_Windows\Run_ISI_Exams.bat
echo ISI_Exams.exe >> ISI_Exams_Windows\Run_ISI_Exams.bat
echo pause >> ISI_Exams_Windows\Run_ISI_Exams.bat

REM Create README
echo ISI Exams Management System - Windows Version > ISI_Exams_Windows\README_Windows.txt
echo ============================================= >> ISI_Exams_Windows\README_Windows.txt
echo. >> ISI_Exams_Windows\README_Windows.txt
echo QUICK START: >> ISI_Exams_Windows\README_Windows.txt
echo 1. Double-click "Run_ISI_Exams.bat" to start the application >> ISI_Exams_Windows\README_Windows.txt
echo 2. Your web browser will open automatically >> ISI_Exams_Windows\README_Windows.txt
echo 3. If the browser doesn't open, go to: http://localhost:8080/seances.html >> ISI_Exams_Windows\README_Windows.txt
echo. >> ISI_Exams_Windows\README_Windows.txt
echo REQUIREMENTS: >> ISI_Exams_Windows\README_Windows.txt
echo - Windows 7 or higher >> ISI_Exams_Windows\README_Windows.txt
echo - No additional software installation required >> ISI_Exams_Windows\README_Windows.txt

REM Show completion message
echo.
echo ========================================
echo BUILD COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo Executable location: ISI_Exams_Windows\
echo Main executable: ISI_Exams_Windows\ISI_Exams.exe
echo Launcher script: ISI_Exams_Windows\Run_ISI_Exams.bat
echo.
echo To distribute:
echo 1. Copy the entire 'ISI_Exams_Windows' folder to target machines
echo 2. Users should run 'Run_ISI_Exams.bat' to start the application
echo.
echo The executable includes all dependencies and the web interface.
echo No additional installation is required on target machines.
echo.

REM Deactivate virtual environment
call deactivate

echo Press any key to exit...
pause >nul
