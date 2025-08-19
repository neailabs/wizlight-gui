"""
Theme Manager for Qt Applications
Handles automatic theme detection and switching between light/dark modes
"""

import os
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QPalette

class ThemeManager(QObject):
    """
    Manages theme switching and detection for Qt applications
    """
    theme_changed = Signal(str)  # Emits 'light' or 'dark'
    
    def __init__(self, app: QApplication = None):
        super().__init__()
        self.app = app or QApplication.instance()
        self.current_theme = None
        
        # Get the base path for bundled resources
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running from a PyInstaller bundle
            base_path = sys._MEIPASS
        else:
            # Running in a normal Python environment
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Construct the correct path to the stylesheet
        stylesheet_path = os.path.join(base_path, 'resources')
        if not os.path.exists(stylesheet_path):
            raise FileNotFoundError(f"Stylesheet directory does not exist: {stylesheet_path}")
        else:
            self.stylesheet_dir = Path(stylesheet_path)

        # self.stylesheet_dir = Path(__file__).parent / "resources"   # Adjust path as needed
        
        # Timer for periodic theme checking
        self.theme_check_timer = QTimer()
        self.theme_check_timer.timeout.connect(self.check_system_theme)
        
        # Initial theme detection
        self.detect_and_apply_theme()
    
    def detect_system_theme(self) -> str:
        """
        Detect the current system theme preference
        Returns: 'light' or 'dark'
        """
        if not self.app:
            return 'light'
        
        # Method 1: Check Qt palette colors
        palette = self.app.palette()
        window_color = palette.color(QPalette.Window)
        text_color = palette.color(QPalette.WindowText)
        
        # If window is darker than text, we're likely in dark mode
        window_brightness = window_color.lightness()
        text_brightness = text_color.lightness()
        
        if window_brightness < text_brightness and window_brightness < 128:
            return 'dark'
        
        # Method 2: macOS specific detection
        if sys.platform == "darwin":
            try:
                import subprocess
                result = subprocess.run([
                    'defaults', 'read', '-g', 'AppleInterfaceStyle'
                ], capture_output=True, text=True)
                
                if result.returncode == 0 and 'Dark' in result.stdout:
                    return 'dark'
            except Exception:
                pass
        
        # Method 3: Windows specific detection
        elif sys.platform == "win32":
            try:
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, 
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return 'light' if value else 'dark'
            except Exception:
                pass
        
        # Method 4: Linux specific detection
        elif sys.platform.startswith("linux"):
            try:
                import subprocess
                # Try GNOME
                result = subprocess.run([
                    'gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'
                ], capture_output=True, text=True)
                
                if result.returncode == 0 and 'dark' in result.stdout.lower():
                    return 'dark'
                
                # Try KDE
                result = subprocess.run([
                    'kreadconfig5', '--group', 'Colors:Window', '--key', 'BackgroundNormal'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Parse RGB values and determine if dark
                    rgb = result.stdout.strip().split(',')
                    if len(rgb) == 3:
                        avg_brightness = sum(int(x) for x in rgb) / 3
                        if avg_brightness < 128:
                            return 'dark'
                            
            except Exception:
                pass
        
        # Default to light theme
        return 'light'
    
    def load_stylesheet(self, theme: str) -> str:
        """
        Load the stylesheet for the specified theme
        Args:
            theme: 'light' or 'dark'
        Returns:
            stylesheet content as string
        """
        stylesheet_file = self.stylesheet_dir / f"styles_{theme}.qss"
        
        try:
            with open(stylesheet_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Stylesheet file not found: {stylesheet_file}")
            return ""
        except Exception as e:
            print(f"Error loading stylesheet: {e}")
            return ""
    
    def apply_theme(self, widget, theme: str = None):
        """
        Apply the specified theme to a widget
        Args:
            widget: The Qt widget to apply the theme to
            theme: 'light', 'dark', or None (auto-detect)
        """
        if theme is None:
            theme = self.detect_system_theme()
        
        stylesheet = self.load_stylesheet(theme)
        if stylesheet:
            widget.setStyleSheet(stylesheet)
            self.current_theme = theme
            self.theme_changed.emit(theme)
            print(f"Applied {theme} theme")
        else:
            print(f"Failed to apply {theme} theme")
    
    def detect_and_apply_theme(self, widget=None):
        """
        Detect system theme and apply to widget(s)
        Args:
            widget: Widget to apply theme to. If None, applies to all top-level widgets
        """
        theme = self.detect_system_theme()
        
        if widget:
            self.apply_theme(widget, theme)
        else:
            # Apply to all top-level widgets
            if self.app:
                for widget in self.app.topLevelWidgets():
                    self.apply_theme(widget, theme)
    
    def toggle_theme(self, widget=None):
        """
        Toggle between light and dark themes
        Args:
            widget: Widget to apply theme to. If None, applies to all top-level widgets
        """
        new_theme = 'dark' if self.current_theme == 'light' else 'light'
        
        if widget:
            self.apply_theme(widget, new_theme)
        else:
            if self.app:
                for widget in self.app.topLevelWidgets():
                    self.apply_theme(widget, new_theme)
    
    def check_system_theme(self):
        """
        Check if system theme has changed and update if necessary
        """
        new_theme = self.detect_system_theme()
        
        if new_theme != self.current_theme:
            print(f"System theme changed from {self.current_theme} to {new_theme}")
            self.detect_and_apply_theme()
    
    def start_theme_monitoring(self, interval_ms: int = 5000):
        """
        Start monitoring system theme changes
        Args:
            interval_ms: Check interval in milliseconds (default: 5 seconds)
        """
        self.theme_check_timer.start(interval_ms)
        print(f"Started theme monitoring (checking every {interval_ms}ms)")
    
    def stop_theme_monitoring(self):
        """Stop monitoring system theme changes"""
        self.theme_check_timer.stop()
        print("Stopped theme monitoring")


# Convenience functions for easy integration
def setup_theme_manager(app: QApplication = None) -> ThemeManager:
    """
    Create and setup a theme manager
    Args:
        app: QApplication instance (optional)
    Returns:
        ThemeManager instance
    """
    theme_manager = ThemeManager(app)
    return theme_manager

def apply_auto_theme(widget, stylesheet_dir: str = None):
    """
    Simple function to apply auto-detected theme to a widget
    Args:
        widget: Qt widget to style
        stylesheet_dir: Directory containing the stylesheet files
    """
    manager = ThemeManager()
    if stylesheet_dir:
        manager.stylesheet_dir = Path(stylesheet_dir)
    manager.apply_theme(widget)
