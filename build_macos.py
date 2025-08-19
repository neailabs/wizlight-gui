#!/usr/bin/env python3
"""
Build script for creating a macOS application bundle
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def create_app_bundle():
    """Create a macOS .app bundle"""
    
    app_name = "WizLight GUI"
    bundle_name = f"{app_name}.app"
    
    # Create bundle structure
    bundle_path = Path(bundle_name)
    contents_path = bundle_path / "Contents"
    macos_path = contents_path / "MacOS"
    resources_path = contents_path / "Resources"
    build_path = contents_path / "build"
    
    # Clean up existing bundle
    if bundle_path.exists():
        shutil.rmtree(bundle_path)
    
    # Create directories
    macos_path.mkdir(parents=True)
    resources_path.mkdir(parents=True)
    build_path.mkdir(parents=True)
    
    # Create Info.plist
    info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>WizLight GUI</string>
    <key>CFBundleIdentifier</key>
    <string>com.wizlight.gui</string>
    <key>CFBundleName</key>
    <string>{app_name}</string>
    <key>CFBundleVersion</key>
    <string>1.1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.1.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>"""
    
    with open(contents_path / "Info.plist", "w") as f:
        f.write(info_plist)
    
    # Create launcher script
    launcher_script = f"""#!/bin/bash
DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" && pwd )"
cd "$DIR/../Resources"
python3 main.py
"""
    
    launcher_path = macos_path / "WizLight GUI"
    with open(launcher_path, "w") as f:
        f.write(launcher_script)
    
    # Make launcher executable
    os.chmod(launcher_path, 0o755)
    
    # Copy application files
    files_to_copy = [
        "main.py",
        "main_window.py", 
        "wizlight_wrapper.py",
        "requirements.txt",
        "theme_manager.py",
        "README.md",
        "LICENSE.md"
    ]
    
    for file in files_to_copy:
        if Path(file).exists():
            shutil.copy2(file, resources_path)
    
    # Copy resources directory
    if Path("resources").exists():
        shutil.copytree("resources", resources_path / "resources")
    
    # Copy wizlightcpp executable
    wizlightcpp_path = Path("../build/wizlightcpp")
    if wizlightcpp_path.exists():
        shutil.copy2(wizlightcpp_path, build_path)
    
    print(f"✅ Created {bundle_name}")
    print(f"📁 Bundle location: {bundle_path.absolute()}")
    print(f"🚀 To run: open '{bundle_name}' or double-click in Finder")
    
    return bundle_path


def install_dependencies():
    """Install required Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def check_wizlightcpp():
    """Check if wizlightcpp executable exists"""
    executable_path = Path("../build/wizlightcpp")
    if executable_path.exists():
        print(f"✅ Found wizlightcpp executable at {executable_path.absolute()}")
        return True
    else:
        print(f"⚠️  wizlightcpp executable not found at {executable_path.absolute()}")
        print("   Make sure to build the C++ project first:")
        print("   cd .. && mkdir build && cd build && cmake .. && make")
        return False


def main():
    """Main build function"""
    print("🔨 Building WizLight GUI Controller for macOS...")
    print()
    
    # Check prerequisites
    if not check_wizlightcpp():
        print("❌ Build failed: wizlightcpp executable not found")
        return 1
    
    if not install_dependencies():
        print("❌ Build failed: Could not install dependencies")
        return 1
    
    # Create app bundle
    try:
        bundle_path = create_app_bundle()
        print()
        print("🎉 Build completed successfully!")
        print()
        print("Next steps:")
        print(f"1. Double-click '{bundle_path.name}' to launch the application")
        print("2. Or run from Terminal: open 'WizLight Controller.app'")
        print()
        print("Note: Make sure your Wiz lights are connected to the same network")
        
        return 0
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
