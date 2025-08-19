#!/usr/bin/env python3
"""
Main entry point for the WizLight GUI application
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from main_window import WizLightMainWindow


def main():
    """Main application entry point"""
    # Create the application
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("WizLight Controller")
    app.setApplicationVersion("1.1.0")
    app.setOrganizationName("WizLight GUI")
    app.setOrganizationDomain("wizlight.local")
    
    # Set application icon if available
    icon_path = current_dir / "resources" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create and show the main window
    try:
        main_window = WizLightMainWindow()
        main_window.show()
        
        # Start the event loop
        return app.exec()
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
