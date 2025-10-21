#!/usr/bin/env python3
"""
Test script to verify the Windows build setup for ISI Exams
This script checks dependencies and validates the build configuration before running the actual build.
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.11 or higher"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11 or higher is required")
        return False
    
    print("✅ Python version is compatible")
    return True

def check_required_files():
    """Check if all required application files exist"""
    required_files = [
        'app.py',
        'seances.py', 
        'enseignants.py',
        'configuration.py',
        'assignements.py',
        'isi_exams.spec',
        'requirements-build.txt',
        'build_windows.sh'
    ]
    
    required_dirs = [
        'web',
        'pdf_generation'
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
        else:
            print(f"✅ {file} found")
    
    for dir_name in required_dirs:
        if not Path(dir_name).is_dir():
            missing_dirs.append(dir_name)
        else:
            print(f"✅ {dir_name}/ directory found")
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    if missing_dirs:
        print(f"❌ Missing required directories: {', '.join(missing_dirs)}")
        return False
    
    return True

def check_build_dependencies():
    """Check if build dependencies can be imported"""
    dependencies = {
        'eel': 'eel',
        'ortools': 'ortools', 
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'weasyprint': 'weasyprint',
        'PyInstaller': 'PyInstaller'
    }
    
    missing_deps = []
    
    for name, module in dependencies.items():
        spec = importlib.util.find_spec(module)
        if spec is None:
            missing_deps.append(name)
            print(f"❌ {name} not found")
        else:
            try:
                # Try to import to check if it's actually working
                __import__(module)
                print(f"✅ {name} is available")
            except ImportError as e:
                missing_deps.append(name)
                print(f"❌ {name} import error: {e}")
    
    if missing_deps:
        print(f"\n📦 Missing dependencies: {', '.join(missing_deps)}")
        print("💡 Install them with: pip install -r requirements-build.txt")
        return False
    
    return True

def check_web_files():
    """Check if essential web files exist"""
    web_files = [
        'web/seances.html',
        'web/enseignants.html', 
        'web/configuration.html',
        'web/assignements.html'
    ]
    
    missing_web_files = []
    
    for file in web_files:
        if not Path(file).exists():
            missing_web_files.append(file)
        else:
            print(f"✅ {file} found")
    
    if missing_web_files:
        print(f"❌ Missing web files: {', '.join(missing_web_files)}")
        return False
    
    return True

def estimate_build_size():
    """Estimate the size of the final build"""
    try:
        # Check size of main components
        web_size = sum(f.stat().st_size for f in Path('web').rglob('*') if f.is_file())
        static_size = 0
        if Path('static').exists():
            static_size = sum(f.stat().st_size for f in Path('static').rglob('*') if f.is_file())
        
        pdf_size = 0
        if Path('pdf_generation').exists():
            pdf_size = sum(f.stat().st_size for f in Path('pdf_generation').rglob('*') if f.is_file())
        
        app_size = sum(Path(f).stat().st_size for f in ['app.py', 'seances.py', 'enseignants.py', 'configuration.py', 'assignements.py'] if Path(f).exists())
        
        total_app_size = (web_size + static_size + pdf_size + app_size) / (1024 * 1024)
        
        print(f"\n📊 Estimated application files size: {total_app_size:.2f} MB")
        print("📊 Expected final executable size: ~250-400 MB (including Python runtime and dependencies)")
        
    except Exception as e:
        print(f"⚠️ Could not estimate build size: {e}")

def check_system_requirements():
    """Check system requirements for building"""
    print("\n🔧 System Requirements Check:")
    
    # Check available disk space
    try:
        stat = os.statvfs('.')
        free_space = (stat.f_bavail * stat.f_frsize) / (1024 * 1024 * 1024)
        print(f"✅ Available disk space: {free_space:.2f} GB")
        
        if free_space < 2:
            print("⚠️ Warning: Less than 2GB free space. Build may fail.")
            
    except AttributeError:
        print("ℹ️ Cannot check disk space on this system")
    
    # Check if Wine is available (for Linux cross-compilation)
    if sys.platform.startswith('linux'):
        try:
            result = subprocess.run(['wine', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Wine found: {result.stdout.strip()}")
            else:
                print("❌ Wine not found (needed for Windows cross-compilation on Linux)")
                print("💡 Install with: sudo apt install wine (Ubuntu/Debian)")
        except FileNotFoundError:
            print("❌ Wine not found (needed for Windows cross-compilation on Linux)")
            print("💡 Install with: sudo apt install wine (Ubuntu/Debian)")

def run_build_test():
    """Run a test to validate the build configuration"""
    print("\n🧪 Running build configuration test...")
    
    try:
        # Test PyInstaller with --help to see if it works
        result = subprocess.run(['pyinstaller', '--help'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ PyInstaller is working")
        else:
            print("❌ PyInstaller test failed")
            return False
            
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ PyInstaller not found or not working")
        return False
    
    # Test spec file syntax
    try:
        with open('isi_exams.spec', 'r') as f:
            spec_content = f.read()
            compile(spec_content, 'isi_exams.spec', 'exec')
        print("✅ PyInstaller spec file syntax is valid")
    except Exception as e:
        print(f"❌ Spec file syntax error: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🔍 ISI Exams - Windows Build Validation")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("Required Files", check_required_files), 
        ("Web Files", check_web_files),
        ("Build Dependencies", check_build_dependencies),
        ("Build Test", run_build_test)
    ]
    
    for check_name, check_func in checks:
        print(f"\n🔎 Checking {check_name}...")
        if not check_func():
            all_checks_passed = False
    
    # Additional system checks
    check_system_requirements()
    estimate_build_size()
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All checks passed! Ready to build Windows executable.")
        print("\n📋 Next steps:")
        print("1. Run: ./build_windows.sh")
        print("2. Wait for build to complete (may take 10-15 minutes)")
        print("3. Distribute the ISI_Exams_Windows folder or ZIP file")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above before building.")
        print("\n💡 Common fixes:")
        print("- Install missing dependencies: pip install -r requirements-build.txt")
        print("- Install Wine on Linux: sudo apt install wine") 
        print("- Ensure all application files are present")
        return 1

if __name__ == "__main__":
    sys.exit(main())
