#!/usr/bin/env bash

# ISI Exams - Windows Build Script for Linux
# This script builds a Windows executable from a Linux system

set -e # Exit on any error

echo "========================================"
echo "ISI Exams - Windows Build Script"
echo "========================================"

# Configuration
APP_NAME="ISI_Exams"
PACKAGE_NAME="ISIExamsSetter"
PYTHON_VERSION="3.11"
BUILD_DIR="build_windows"
DIST_DIR="dist_windows"
REQUIREMENTS_FILE="requirements-build.txt"
SPEC_FILE="isi_exams.spec"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_error "This script is designed to run on Linux systems only."
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
print_status "Checking required tools..."

if ! command_exists uv; then
    print_error "uv is not installed!"
    print_status "Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

if ! command_exists python3; then
    print_error "Python 3 is not installed!"
    exit 1
fi

# Check Python version
PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
print_status "Python version: $PYTHON_VER"

# Create virtual environment for clean build
print_status "Creating virtual environment for Windows build..."
if [ -d "venv_windows_build" ]; then
    print_warning "Removing existing virtual environment..."
    rm -rf venv_windows_build
fi

uv venv venv_windows_build
source venv_windows_build/bin/activate

# Install build requirements
print_status "Installing build dependencies..."
if [ -f "$REQUIREMENTS_FILE" ]; then
    uv pip install -r "$REQUIREMENTS_FILE"
else
    print_error "Requirements file $REQUIREMENTS_FILE not found!"
    exit 1
fi

# Install Wine if not present (for Windows builds on Linux)
if ! command_exists wine; then
    print_warning "Wine is not installed. Installing Wine for Windows builds..."
    print_status "Adding Wine repository..."

    # Add Wine repository (Ubuntu/Debian)
    if command_exists apt-get; then
        sudo dpkg --add-architecture i386
        sudo mkdir -pm755 /etc/apt/keyrings
        sudo wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key
        sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/$(lsb_release -cs)/winehq-$(lsb_release -cs).sources
        sudo apt update
        sudo apt install -y winehq-stable
    else
        print_error "Please install Wine manually for Windows cross-compilation"
        print_status "On Ubuntu/Debian: sudo apt install wine"
        print_status "On Fedora: sudo dnf install wine"
        print_status "On Arch: sudo pacman -S wine"
        exit 1
    fi
fi

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$DIST_DIR" __pycache__ *.pyc
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Verify all required files exist
print_status "Verifying required files..."
required_files=("app.py" "seances.py" "enseignants.py" "configuration.py" "assignements.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file $file not found!"
        exit 1
    fi
done

# Check if web directory exists
if [ ! -d "web" ]; then
    print_error "Web directory not found! This is required for the Eel application."
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Build the Windows executable
print_status "Building Windows executable with PyInstaller..."
print_status "This may take several minutes..."

# Set environment variables for Windows cross-compilation
export PYINSTALLER_CONFIG_DIR="/tmp/pyinstaller_cache"
mkdir -p "$PYINSTALLER_CONFIG_DIR"

# Common PyInstaller arguments for Windows 10 64-bit compatibility
PYINSTALLER_ARGS=(
    "--clean"
    "--distpath" "$DIST_DIR"
    "--workpath" "$BUILD_DIR"
    "--name" "$APP_NAME"
    "--target-architecture" "x86_64"
    "--add-data" "web${PATH_SEPARATOR}web"
    "--add-data" "pdf_generation${PATH_SEPARATOR}pdf_generation"
    "--add-data" "static${PATH_SEPARATOR}static"
    "--hidden-import" "eel"
    "--hidden-import" "seances"
    "--hidden-import" "enseignants"
    "--hidden-import" "configuration"
    "--hidden-import" "assignements"
    "--hidden-import" "ortools.sat.python.cp_model"
    "--hidden-import" "weasyprint"
    "--hidden-import" "pandas"
    "--hidden-import" "openpyxl"
    "--hidden-import" "pydantic"
    "--hidden-import" "json"
    "--hidden-import" "csv"
    "--hidden-import" "pickle"
    "--hidden-import" "datetime"
    "--hidden-import" "traceback"
    "--hidden-import" "tempfile"
    "--hidden-import" "zipfile"
    "--noconfirm"
    "--log-level" "INFO"
)

# Set path separator for cross-platform compatibility
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    PATH_SEPARATOR=";"
else
    PATH_SEPARATOR=":"
fi

# Update PyInstaller args with correct path separator
PYINSTALLER_ARGS=(
    "--clean"
    "--distpath" "$DIST_DIR"
    "--workpath" "$BUILD_DIR"
    "--name" "$APP_NAME"
    "--target-architecture" "x86_64"
    "--add-data" "web${PATH_SEPARATOR}web"
    "--add-data" "pdf_generation${PATH_SEPARATOR}pdf_generation"
    "--add-data" "static${PATH_SEPARATOR}static"
    "--hidden-import" "eel"
    "--hidden-import" "seances"
    "--hidden-import" "enseignants"
    "--hidden-import" "configuration"
    "--hidden-import" "assignements"
    "--hidden-import" "ortools.sat.python.cp_model"
    "--hidden-import" "weasyprint"
    "--hidden-import" "pandas"
    "--hidden-import" "openpyxl"
    "--hidden-import" "pydantic"
    "--noconfirm"
    "--log-level" "INFO"
)

# Handle NixOS-specific issues with shared libraries
if [ -f /etc/NIXOS ]; then
    print_status "Detected NixOS - setting up environment for PyInstaller..."

    # Try to use the spec file first with NixOS modifications
    if [ -f "$SPEC_FILE" ]; then
        print_status "Using spec file: $SPEC_FILE"
        pyinstaller "${PYINSTALLER_ARGS[@]}" "$SPEC_FILE"
    else
        print_warning "Spec file not found, building directly..."
        pyinstaller "${PYINSTALLER_ARGS[@]}" app.py
    fi
else
    # Standard build for non-NixOS systems
    if [ -f "$SPEC_FILE" ]; then
        print_status "Using spec file: $SPEC_FILE"
        pyinstaller --clean --distpath "$DIST_DIR" --workpath "$BUILD_DIR" --target-architecture x86_64 "$SPEC_FILE"
    else
        print_warning "Spec file not found, building directly with full arguments..."
        pyinstaller "${PYINSTALLER_ARGS[@]}" app.py
    fi
fi

# Check if build was successful and handle executable naming
EXECUTABLE_NAME=""
BUILD_SUCCESS=false

if [ -d "$DIST_DIR/$APP_NAME" ]; then
    print_success "Directory-based build completed successfully!"
    BUILD_SUCCESS=true
    # Look for the main executable in the directory
    if [ -f "$DIST_DIR/$APP_NAME/$APP_NAME.exe" ]; then
        EXECUTABLE_NAME="$APP_NAME.exe"
    elif [ -f "$DIST_DIR/$APP_NAME/$APP_NAME" ]; then
        EXECUTABLE_NAME="$APP_NAME"
    else
        # Find any executable in the directory
        EXECUTABLE_NAME=$(find "$DIST_DIR/$APP_NAME" -maxdepth 1 -type f -executable | head -1 | xargs basename)
    fi
elif [ -f "$DIST_DIR/$APP_NAME.exe" ]; then
    print_success "Single-file build completed successfully!"
    BUILD_SUCCESS=true
    EXECUTABLE_NAME="$APP_NAME.exe"
elif [ -f "$DIST_DIR/$APP_NAME" ]; then
    print_success "Build completed (no .exe extension)!"
    BUILD_SUCCESS=true
    EXECUTABLE_NAME="$APP_NAME"
fi

if [ "$BUILD_SUCCESS" = true ]; then
    print_success "Build completed successfully!"
    print_status "Executable found: $EXECUTABLE_NAME"

    # Create ISIExamsSetter folder structure
    print_status "Creating ISIExamsSetter package..."

    PACKAGE_DIR="$PACKAGE_NAME"
    rm -rf "$PACKAGE_DIR"
    mkdir -p "$PACKAGE_DIR"

    # Copy the executable and its dependencies
    if [ -d "$DIST_DIR/$APP_NAME" ]; then
        # Directory-based build (standard spec file)
        cp -r "$DIST_DIR/$APP_NAME/"* "$PACKAGE_DIR/"

        # Ensure the main executable has .exe extension for Windows compatibility
        if [ -f "$PACKAGE_DIR/$EXECUTABLE_NAME" ] && [[ "$EXECUTABLE_NAME" != *.exe ]]; then
            print_status "Renaming executable to add .exe extension for Windows compatibility..."
            mv "$PACKAGE_DIR/$EXECUTABLE_NAME" "$PACKAGE_DIR/$APP_NAME.exe"
            EXECUTABLE_NAME="$APP_NAME.exe"
        fi
    elif [ -f "$DIST_DIR/$EXECUTABLE_NAME" ]; then
        # Single file build
        if [[ "$EXECUTABLE_NAME" == *.exe ]]; then
            cp "$DIST_DIR/$EXECUTABLE_NAME" "$PACKAGE_DIR/$APP_NAME.exe"
        else
            # Add .exe extension if missing
            cp "$DIST_DIR/$EXECUTABLE_NAME" "$PACKAGE_DIR/$APP_NAME.exe"
            print_status "Added .exe extension for Windows compatibility"
        fi
        EXECUTABLE_NAME="$APP_NAME.exe"
    fi

    # Always copy necessary directories for Windows 10 compatibility
    print_status "Copying web and static folders..."
    if [ -d "web" ]; then
        cp -r web "$PACKAGE_DIR/"
        print_success "Copied web folder"
    else
        print_warning "Web folder not found!"
    fi

    if [ -d "static" ]; then
        cp -r static "$PACKAGE_DIR/"
        print_success "Copied static folder"
    else
        print_warning "Static folder not found!"
    fi

    # Copy additional required directories if they exist
    [ -d "data" ] && cp -r data "$PACKAGE_DIR/" && print_success "Copied data folder"
    [ -d "pdf_generation" ] && cp -r pdf_generation "$PACKAGE_DIR/" && print_success "Copied pdf_generation folder"

    # Create a simple batch file to run the application
    cat >"$PACKAGE_DIR/Run_ISI_Exams.bat" <<EOF
@echo off
title ISI Exams Management System
echo ========================================
echo ISI Exams Management System
echo Windows 10 64-bit Compatible Version
echo ========================================
echo.
echo Starting application...
echo Please wait while the system loads...
echo.
echo Once loaded, your web browser will open automatically.
echo If the browser doesn't open automatically, please go to:
echo http://localhost:8080/seances.html
echo.
echo Press Ctrl+C to stop the application.
echo.

REM Check if the executable exists
if not exist "$APP_NAME.exe" (
    echo ERROR: $APP_NAME.exe not found!
    echo Please make sure all files are in the same directory.
    pause
    exit /b 1
)

REM Run the application
"$APP_NAME.exe"

REM If we get here, the application has closed
echo.
echo Application has stopped.
pause
EOF

    # Create a README for Windows users
    cat >"$PACKAGE_DIR/README_Windows.txt" <<EOF
ISI Exams Management System - Windows 10 64-bit Version
=======================================================

SYSTEM REQUIREMENTS:
- Windows 10 (64-bit) or Windows 11
- Minimum 4GB RAM recommended
- Internet connection (for web interface)
- No additional software installation required

QUICK START:
1. Extract all files to a folder (if using ZIP)
2. Double-click "Run_ISI_Exams.bat" to start the application
3. Wait for the application to load (may take 30-60 seconds on first run)
4. Your web browser will open automatically to the application interface
5. If the browser doesn't open, manually go to: http://localhost:8080/seances.html

IMPORTANT NOTES:
- This is a 64-bit application designed for Windows 10/11
- All files must remain in the same folder
- Do not rename or move the $APP_NAME.exe file
- The application runs locally on your computer (no internet required after startup)

TROUBLESHOOTING:
- Windows Security Warning: Click "More info" then "Run anyway"
- Antivirus Software: Add the folder to your antivirus exceptions
- Port 8080 in use: Close other applications that might use this port
- Slow startup: This is normal on first run, subsequent runs will be faster
- Admin Rights: If you have issues, try "Run as Administrator"

FIREWALL NOTICE:
Windows may ask for firewall permission. Click "Allow access" to enable
the web interface to work properly.

APPLICATION FEATURES:
- Exam session and schedule management
- Teacher and room assignment optimization  
- Import/export data (CSV, Excel formats)
- PDF report generation for surveillance schedules
- Web-based user interface (modern browsers supported)

TECHNICAL SUPPORT:
- Keep all files together in one folder
- Check Windows Event Viewer for detailed error messages if issues occur
- Ensure Windows 10 is updated to latest version for best compatibility

Version: Windows 10 64-bit Compatible
Build Date: $(date)
EOF

    # Create ZIP package for easy distribution
    print_status "Creating ZIP package for distribution..."
    ZIP_NAME="${PACKAGE_NAME}_$(date +%Y%m%d_%H%M%S).zip"

    if command_exists zip; then
        cd "$PACKAGE_DIR"
        zip -r "../$ZIP_NAME" .
        cd ..
        print_success "ZIP package created: $ZIP_NAME"
    else
        print_warning "zip command not found. Manual packaging required."
    fi

    # Show package contents
    print_status "Package contents:"
    ls -la "$PACKAGE_DIR/"

    # Show size information
    PACKAGE_SIZE=$(du -sh "$PACKAGE_DIR" | cut -f1)
    print_success "Package size: $PACKAGE_SIZE"

    print_success "Windows 10 64-bit executable build completed!"
    echo ""
    echo "========================================"
    echo "BUILD SUMMARY - WINDOWS 10 64-BIT"
    echo "========================================"
    echo "✓ Package folder: $PACKAGE_DIR/"
    echo "✓ Main executable: $PACKAGE_DIR/$EXECUTABLE_NAME"
    echo "✓ Launcher script: $PACKAGE_DIR/Run_ISI_Exams.bat"
    echo "✓ Web folder: $PACKAGE_DIR/web/"
    echo "✓ Static folder: $PACKAGE_DIR/static/"
    echo "✓ Architecture: x86_64 (64-bit Windows compatible)"
    echo "✓ Package size: $PACKAGE_SIZE"
    if [ -f "$ZIP_NAME" ]; then
        echo "✓ ZIP package: $ZIP_NAME"
    fi
    echo ""
    echo "Windows 10/11 Ready Package:"
    echo "1. Copy the '$PACKAGE_DIR' folder to any Windows 10+ (64-bit) machine"
    echo "2. Or distribute the ZIP file: $ZIP_NAME"
    echo "3. Users should run 'Run_ISI_Exams.bat' to start the application"
    echo "4. Compatible with Windows 10, Windows 11 (64-bit systems only)"
    echo ""
    echo "The executable includes all dependencies and the web interface."
    echo "No additional installation is required on the target Windows machine."

else
    print_error "Build failed! Please check the output above for errors."
    exit 1
fi

# Deactivate virtual environment
deactivate

print_success "All done!"
