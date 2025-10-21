# Windows Build Script for ISI Exams Management System
# PowerShell version - more robust than batch script

param(
    [switch]$Clean = $false,
    [switch]$Verbose = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Blue
Write-Host "ISI Exams - Windows Build Script (PowerShell)" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Configuration
$AppName = "ISI_Exams"
$BuildDir = "build_windows"
$DistDir = "dist_windows"
$PackageDir = "ISI_Exams_Windows"
$RequirementsFile = "requirements-build.txt"
$SpecFile = "isi_exams.spec"
$VenvDir = "venv_windows_build"

# Function to write colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if running on Windows
if ($PSVersionTable.Platform -and $PSVersionTable.Platform -ne "Win32NT") {
    Write-Error "This script is designed to run on Windows systems only."
    exit 1
}

# Check if Python is installed
Write-Status "Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Status "Python found: $pythonVersion"
    
    # Check Python version (should be 3.11+)
    $versionCheck = python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python 3.11 or higher is required. Please upgrade your Python installation."
        exit 1
    }
} catch {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.11+ from https://python.org"
    exit 1
}

# Check if pip is available
try {
    python -m pip --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "pip not found"
    }
} catch {
    Write-Error "pip is not available. Please ensure pip is installed with Python."
    exit 1
}

# Clean previous builds if requested
if ($Clean) {
    Write-Status "Cleaning previous builds..."
    @($BuildDir, $DistDir, $PackageDir, $VenvDir) | ForEach-Object {
        if (Test-Path $_) {
            Remove-Item $_ -Recurse -Force
            Write-Status "Removed $_"
        }
    }
}

# Create virtual environment
Write-Status "Creating virtual environment..."
if (Test-Path $VenvDir) {
    Write-Warning "Removing existing virtual environment..."
    Remove-Item $VenvDir -Recurse -Force
}

python -m venv $VenvDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create virtual environment"
    exit 1
}

# Activate virtual environment
Write-Status "Activating virtual environment..."
$activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-Error "Failed to find activation script at $activateScript"
    exit 1
}

# Upgrade pip
Write-Status "Upgrading pip..."
python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to upgrade pip"
    exit 1
}

# Install build requirements
Write-Status "Installing build dependencies..."
if (-not (Test-Path $RequirementsFile)) {
    Write-Error "Requirements file $RequirementsFile not found!"
    exit 1
}

python -m pip install -r $RequirementsFile
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install build requirements"
    exit 1
}

# Verify required files exist
Write-Status "Verifying required files..."
$requiredFiles = @("app.py", "seances.py", "enseignants.py", "configuration.py", "assignements.py", $SpecFile)
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Error "Required file $file not found!"
        exit 1
    }
}

# Check if web directory exists
if (-not (Test-Path "web" -PathType Container)) {
    Write-Error "Web directory not found! This is required for the Eel application."
    exit 1
}

# Create data directory if it doesn't exist
if (-not (Test-Path "data" -PathType Container)) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Status "Created data directory"
}

# Clean previous builds
Write-Status "Cleaning previous PyInstaller builds..."
@($BuildDir, $DistDir) | ForEach-Object {
    if (Test-Path $_) {
        Remove-Item $_ -Recurse -Force
    }
}

# Build the Windows executable
Write-Status "Building Windows executable with PyInstaller..."
Write-Status "This may take several minutes..."

$pyinstallerArgs = @(
    "--clean",
    "--distpath", $DistDir,
    "--workpath", $BuildDir,
    $SpecFile
)

if ($Verbose) {
    $pyinstallerArgs += "--log-level=DEBUG"
}

pyinstaller @pyinstallerArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed!"
    exit 1
}

# Check if build was successful
$exePath = Join-Path $DistDir $AppName
if (-not (Test-Path $exePath -PathType Container)) {
    Write-Error "Build failed! Expected directory $exePath not found."
    exit 1
}

Write-Success "Build completed successfully!"

# Create user-friendly package
Write-Status "Creating user-friendly package..."
if (Test-Path $PackageDir) {
    Remove-Item $PackageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $PackageDir | Out-Null

# Copy the executable and its dependencies
Copy-Item -Path "$exePath\*" -Destination $PackageDir -Recurse
Write-Status "Copied executable files"

# Create launcher batch file
$launcherContent = @"
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
"@

$launcherPath = Join-Path $PackageDir "Run_ISI_Exams.bat"
$launcherContent | Out-File -FilePath $launcherPath -Encoding ascii
Write-Status "Created launcher script"

# Create README for Windows users
$readmeContent = @"
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
"@

$readmePath = Join-Path $PackageDir "README_Windows.txt"
$readmeContent | Out-File -FilePath $readmePath -Encoding utf8
Write-Status "Created README file"

# Calculate package size
$packageSize = (Get-ChildItem $PackageDir -Recurse | Measure-Object -Property Length -Sum).Sum
$packageSizeMB = [math]::Round($packageSize / 1MB, 2)

# Create ZIP package if possible
$zipName = "${AppName}_Windows_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory($PackageDir, $zipName)
    Write-Success "ZIP package created: $zipName"
    $hasZip = $true
} catch {
    Write-Warning "Could not create ZIP package: $_"
    $hasZip = $false
}

# Show package contents
Write-Status "Package contents:"
Get-ChildItem $PackageDir | Format-Table Name, Length, LastWriteTime

Write-Success "Windows executable build completed!"
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "BUILD SUMMARY" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Executable location: $PackageDir\" -ForegroundColor Green
Write-Host "✓ Main executable: $PackageDir\ISI_Exams.exe" -ForegroundColor Green
Write-Host "✓ Launcher script: $PackageDir\Run_ISI_Exams.bat" -ForegroundColor Green
Write-Host "✓ Package size: $packageSizeMB MB" -ForegroundColor Green
if ($hasZip) {
    Write-Host "✓ ZIP package: $zipName" -ForegroundColor Green
}
Write-Host ""
Write-Host "To distribute:" -ForegroundColor Yellow
Write-Host "1. Copy the entire '$PackageDir' folder to a Windows machine" -ForegroundColor Yellow
if ($hasZip) {
    Write-Host "2. Or distribute the ZIP file: $zipName" -ForegroundColor Yellow
}
Write-Host "3. Users should run 'Run_ISI_Exams.bat' to start the application" -ForegroundColor Yellow
Write-Host ""
Write-Host "The executable includes all dependencies and the web interface." -ForegroundColor Cyan
Write-Host "No additional installation is required on the target Windows machine." -ForegroundColor Cyan

# Deactivate virtual environment
deactivate

Write-Success "All done!"
