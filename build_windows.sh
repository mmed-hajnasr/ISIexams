#!/usr/bin/env bash

# ISI Exams - Windows Build Script for Linux
# This script builds a Windows executable from a Linux system

set -e # Exit on any error

echo "========================================"
echo "ISI Exams - Windows Build Script"
echo "========================================"

# Configuration
APP_NAME="ISI_Exams"
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

if ! command_exists python3; then
    print_error "Python 3 is not installed!"
    exit 1
fi

if ! command_exists pip3; then
    print_error "pip3 is not installed!"
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

python3 -m venv venv_windows_build
source venv_windows_build/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
python -m pip install --upgrade pip

# Install build requirements
print_status "Installing build dependencies..."
if [ -f "$REQUIREMENTS_FILE" ]; then
    pip install -r "$REQUIREMENTS_FILE"
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

# Use the spec file for detailed configuration
pyinstaller --clean --distpath "$DIST_DIR" --workpath "$BUILD_DIR" "$SPEC_FILE"

# Check if build was successful
if [ -d "$DIST_DIR/$APP_NAME" ]; then
    print_success "Build completed successfully!"
    
    # Create a more user-friendly structure
    print_status "Creating user-friendly package..."
    
    PACKAGE_DIR="${APP_NAME}_Windows"
    rm -rf "$PACKAGE_DIR"
    mkdir -p "$PACKAGE_DIR"
    
    # Copy the executable and its dependencies
    cp -r "$DIST_DIR/$APP_NAME/"* "$PACKAGE_DIR/"
    
    # Create a simple batch file to run the application
    cat > "$PACKAGE_DIR/Run_ISI_Exams.bat" << 'EOF'
@echo off
echo Starting ISI Exams Management System...
echo.
echo Please wait while the application loads...
echo Once loaded, your web browser will open automatically.
echo.
echo If the browser doesn't open automatically, please go to:
echo http://localhost:8080/seances.html
echo.
ISI_Exams.exe
pause
EOF
    
    # Create a README for Windows users
    cat > "$PACKAGE_DIR/README_Windows.txt" << 'EOF'
ISI Exams Management System - Windows Version
=============================================

QUICK START:
1. Double-click "Run_ISI_Exams.bat" to start the application
2. Your web browser will open automatically
3. If the browser doesn't open, go to: http://localhost:8080/seances.html

REQUIREMENTS:
- Windows 7 or higher
- No additional software installation required (everything is included)

TROUBLESHOOTING:
- If Windows shows a security warning, click "More info" then "Run anyway"
- If antivirus software blocks the executable, add it to your exceptions
- Make sure port 8080 is not used by other applications
- If you have issues, try running as Administrator

FEATURES:
- Manage exam sessions and schedules
- Import/export teacher and exam data
- Automatic teacher assignment optimization
- Generate PDF reports for surveillance and schedules

For support or issues, please contact the system administrator.
EOF
    
    # Create ZIP package for easy distribution
    print_status "Creating ZIP package for distribution..."
    ZIP_NAME="${APP_NAME}_Windows_$(date +%Y%m%d_%H%M%S).zip"
    
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
    
    print_success "Windows executable build completed!"
    echo ""
    echo "========================================"
    echo "BUILD SUMMARY"
    echo "========================================"
    echo "✓ Executable location: $PACKAGE_DIR/"
    echo "✓ Main executable: $PACKAGE_DIR/ISI_Exams.exe"
    echo "✓ Launcher script: $PACKAGE_DIR/Run_ISI_Exams.bat"
    echo "✓ Package size: $PACKAGE_SIZE"
    if [ -f "$ZIP_NAME" ]; then
        echo "✓ ZIP package: $ZIP_NAME"
    fi
    echo ""
    echo "To distribute:"
    echo "1. Copy the entire '$PACKAGE_DIR' folder to a Windows machine"
    echo "2. Or distribute the ZIP file: $ZIP_NAME"
    echo "3. Users should run 'Run_ISI_Exams.bat' to start the application"
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
