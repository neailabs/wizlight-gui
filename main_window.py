"""
Main window for the WizLight GUI application
"""

import sys
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QSlider, QSpinBox, QComboBox, QListWidget,
    QListWidgetItem, QGroupBox, QGridLayout, QTextEdit, QProgressBar,
    QMessageBox, QLineEdit, QFrame, QSplitter, QColorDialog
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize
from PySide6.QtGui import QColor, QPalette, QFont, QIcon, QPixmap, QPainter

from wizlight_wrapper import WizLightWrapper, WizLightError
from theme_manager import ThemeManager


class DeviceDiscoveryThread(QThread):
    """Thread for device discovery to prevent UI blocking"""
    devices_found = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, broadcast_ip: str = "192.168.1.255"):
        super().__init__()
        self.broadcast_ip = broadcast_ip
        self.wiz_wrapper = None
    
    def run(self):
        try:
            self.wiz_wrapper = WizLightWrapper()
            devices = self.wiz_wrapper.discover_devices(self.broadcast_ip)
            self.devices_found.emit(devices)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MultiNetworkDiscoveryThread(QThread):
    """Thread for multi-network device discovery"""
    devices_found = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.wiz_wrapper = None
    
    def run(self):
        try:
            self.wiz_wrapper = WizLightWrapper()
            devices = self.wiz_wrapper.discover_devices_multi_network()
            self.devices_found.emit(devices)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ColorPreviewWidget(QWidget):
    """Custom widget to show color preview"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.color = QColor(255, 255, 255)
    
    def set_color(self, r: int, g: int, b: int):
        self.color = QColor(r, g, b)
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.color)
        painter.setPen(Qt.black)
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 8, 8)

class AppConfig:
    """Application configuration constants."""
        
    # Window settings
    WINDOW_TITLE = "Wizlight Controller"
    
    # UI settings
    INPUT_FIELD_WIDTH = 300
    SPINBOX_MIN = 1
    SPINBOX_MAX = 255
    
    # Colors
    BRAND_COLOR = "#EF275D"
    ACCENT_COLOR = "#2FC0F2"
    
    # Company info
    COMPANY_NAME = "NE AI Innovation Labs"
    COMPANY_URL = "https://www.neailabs.com"

class SimpleStatusBarWithCredits:
    """
    Simple implementation using standard QStatusBar methods
    """
    @staticmethod
    def setup_status_bar_with_credits(main_window: QMainWindow):
        """
        Setup status bar with credits using standard QStatusBar
        Args:
            main_window: The main window to add status bar to
        """
        status_bar = main_window.statusBar()
        
        # Create credits label
        credits_label = QLabel(
            f'Created by <a href="{AppConfig.COMPANY_URL}" '
            f'style="color: {AppConfig.BRAND_COLOR}; text-decoration: none;">'
            f'{AppConfig.COMPANY_NAME}</a>'
        )
        credits_label.setOpenExternalLinks(True)
        credits_label.setStyleSheet("""
            font-size: 11px; 
            color: #9ca3af;
            background: transparent;
            padding: 2px 8px;
        """)
        credits_label.setToolTip(f"Visit {AppConfig.COMPANY_URL}")
        
        # Add separator
        separator = QLabel(" | ")
        separator.setStyleSheet("color: #d1d5db; font-size: 11px;")
        
        # Add permanent widgets to right side
        status_bar.addPermanentWidget(separator)
        status_bar.addPermanentWidget(credits_label)
        
        return status_bar
        
class SceneButton(QPushButton):
    """Custom button for scene selection"""
    
    def __init__(self, scene_id: int, scene_name: str, parent=None):
        super().__init__(parent)
        self.scene_id = scene_id
        self.scene_name = scene_name
        self.setText(f"{scene_id}. {scene_name}")
        self.setMinimumHeight(40)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #007bff;
            }
            QPushButton:pressed {
                background-color: #007bff;
                color: white;
            }
        """)


class WizLightMainWindow(QMainWindow):
    """Main window for the WizLight GUI application"""
    
    def __init__(self):
        super().__init__()
        self.wiz_wrapper = None
        self.current_device_ip = None
        self.devices = []
        
        self.init_wrapper()
        self.init_ui()
        
        # Setup custom status bar with credits
        self.custom_status_bar = SimpleStatusBarWithCredits()
        
        # Setup theme manager
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
        
        # Apply initial theme (auto-detects system preference)
        self.theme_manager.apply_theme(self)
        
        # Optional: Monitor system theme changes
        self.theme_manager.start_theme_monitoring()
        self.setup_timers()
    
    def init_wrapper(self):
        """Initialize the WizLight wrapper"""
        try:
            self.wiz_wrapper = WizLightWrapper()
        except WizLightError as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize WizLight wrapper:\n{str(e)}")
            sys.exit(1)
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("WizLight Controller")
        self.setMinimumSize(1280, 900)
        self.resize(1920, 1080)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Device list
        self.create_device_panel(splitter)
        
        # Right panel - Control tabs
        self.create_control_panel(splitter)
        
        # Set splitter proportions
        splitter.setSizes([250, 750])
        
        SimpleStatusBarWithCredits.setup_status_bar_with_credits(self)
        
        # Status bar
        self.statusBar().showMessage("Ready")

    def on_theme_changed(self, theme):
        """Called whenever theme changes"""
        print(f"Theme changed to: {theme}")
        # You can update any theme-dependent elements here
    
    def create_device_panel(self, parent):
        """Create the device discovery and selection panel"""
        device_widget = QWidget()
        device_layout = QVBoxLayout(device_widget)
        
        # Discovery section
        discovery_group = QGroupBox("Device Discovery")
        discovery_layout = QVBoxLayout(discovery_group)
        
        # Broadcast IP input
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("Broadcast IP:"))
        self.broadcast_ip_input = QLineEdit()
        ip_layout.addWidget(self.broadcast_ip_input)
        
        # Auto-detect button
        self.auto_detect_btn = QPushButton("Auto")
        self.auto_detect_btn.setMaximumWidth(60)
        self.auto_detect_btn.clicked.connect(self.auto_detect_broadcast)
        self.auto_detect_btn.setToolTip("Auto-detect broadcast IP for current network")
        ip_layout.addWidget(self.auto_detect_btn)
        
        discovery_layout.addLayout(ip_layout)
        
        # Discovery buttons
        discover_buttons_layout = QHBoxLayout()
        
        self.discover_btn = QPushButton("Discover Devices")
        self.discover_btn.clicked.connect(self.discover_devices)
        discover_buttons_layout.addWidget(self.discover_btn)
        
        self.discover_all_btn = QPushButton("Scan All Networks")
        self.discover_all_btn.clicked.connect(self.discover_all_networks)
        self.discover_all_btn.setToolTip("Scan multiple common network ranges")
        discover_buttons_layout.addWidget(self.discover_all_btn)
        
        discovery_layout.addLayout(discover_buttons_layout)
        
        # Progress bar
        self.discovery_progress = QProgressBar()
        self.discovery_progress.setVisible(False)
        discovery_layout.addWidget(self.discovery_progress)
        
        device_layout.addWidget(discovery_group)
        
        # Device list
        devices_group = QGroupBox("Discovered Devices")
        devices_layout = QVBoxLayout(devices_group)
        
        self.device_list = QListWidget()
        self.device_list.itemClicked.connect(self.on_device_selected)
        devices_layout.addWidget(self.device_list)
        
        device_layout.addWidget(devices_group)
        
        # Current device info
        current_group = QGroupBox("Current Device")
        current_layout = QVBoxLayout(current_group)
        
        self.current_device_label = QLabel("No device selected")
        self.current_device_label.setWordWrap(True)
        current_layout.addWidget(self.current_device_label)
        
        self.refresh_status_btn = QPushButton("Refresh Status")
        self.refresh_status_btn.clicked.connect(self.refresh_device_status)
        self.refresh_status_btn.setEnabled(False)
        current_layout.addWidget(self.refresh_status_btn)
        
        device_layout.addWidget(current_group)
        
        device_layout.addStretch()
        parent.addWidget(device_widget)
    
    def create_control_panel(self, parent):
        """Create the main control panel with tabs"""
        self.tab_widget = QTabWidget()
        
        # Control tab
        self.create_control_tab()
        
        # Scenes tab
        self.create_scenes_tab()
        
        # Device info tab
        self.create_device_info_tab()
        
        parent.addWidget(self.tab_widget)
    
    def create_control_tab(self):
        """Create the main control tab"""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # Power controls
        power_group = QGroupBox("Power Control")
        power_layout = QHBoxLayout(power_group)
        
        self.on_btn = QPushButton("Turn On")
        self.on_btn.clicked.connect(lambda: self.toggle_light(True))
        self.on_btn.setEnabled(False)
        self.on_btn.setStyleSheet("QPushButton { background-color: #66CDAA; color: black; font-weight: bold; }")
        
        self.off_btn = QPushButton("Turn Off")
        self.off_btn.clicked.connect(lambda: self.toggle_light(False))
        self.off_btn.setEnabled(False)
        self.off_btn.setStyleSheet("QPushButton { background-color: #F7806F; color: black; font-weight: bold; }")
        
        power_layout.addWidget(self.on_btn)
        power_layout.addWidget(self.off_btn)
        control_layout.addWidget(power_group)
        
        # Brightness control
        brightness_group = QGroupBox("Brightness")
        brightness_layout = QVBoxLayout(brightness_group)
        
        brightness_controls = QHBoxLayout()
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(50)
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)
        self.brightness_slider.setEnabled(False)
        
        self.brightness_spinbox = QSpinBox()
        self.brightness_spinbox.setRange(0, 100)
        self.brightness_spinbox.setValue(50)
        self.brightness_spinbox.setSuffix("%")
        self.brightness_spinbox.valueChanged.connect(self.brightness_slider.setValue)
        self.brightness_spinbox.setEnabled(False)
        
        self.brightness_slider.valueChanged.connect(self.brightness_spinbox.setValue)
        
        brightness_controls.addWidget(QLabel("Brightness:"))
        brightness_controls.addWidget(self.brightness_slider)
        brightness_controls.addWidget(self.brightness_spinbox)
        brightness_layout.addLayout(brightness_controls)
        
        control_layout.addWidget(brightness_group)
        
        # RGB Color control
        rgb_group = QGroupBox("RGB Color")
        rgb_layout = QVBoxLayout(rgb_group)
        
        # Color preview and picker
        color_preview_layout = QHBoxLayout()
        self.color_preview = ColorPreviewWidget()
        color_preview_layout.addWidget(QLabel("Preview:"))
        color_preview_layout.addWidget(self.color_preview)
        
        self.color_picker_btn = QPushButton("Choose Color")
        self.color_picker_btn.clicked.connect(self.open_color_picker)
        self.color_picker_btn.setEnabled(False)
        color_preview_layout.addWidget(self.color_picker_btn)
        color_preview_layout.addStretch()
        
        rgb_layout.addLayout(color_preview_layout)
        
        # RGB sliders
        rgb_sliders_layout = QGridLayout()
        
        # Red
        rgb_sliders_layout.addWidget(QLabel("Red:"), 0, 0)
        self.red_slider = QSlider(Qt.Horizontal)
        self.red_slider.setRange(0, 255)
        self.red_slider.setValue(255)
        self.red_slider.valueChanged.connect(self.on_rgb_changed)
        self.red_slider.setEnabled(False)
        rgb_sliders_layout.addWidget(self.red_slider, 0, 1)
        
        self.red_spinbox = QSpinBox()
        self.red_spinbox.setRange(0, 255)
        self.red_spinbox.setValue(255)
        self.red_spinbox.valueChanged.connect(self.red_slider.setValue)
        self.red_spinbox.setEnabled(False)
        rgb_sliders_layout.addWidget(self.red_spinbox, 0, 2)
        
        # Green
        rgb_sliders_layout.addWidget(QLabel("Green:"), 1, 0)
        self.green_slider = QSlider(Qt.Horizontal)
        self.green_slider.setRange(0, 255)
        self.green_slider.setValue(255)
        self.green_slider.valueChanged.connect(self.on_rgb_changed)
        self.green_slider.setEnabled(False)
        rgb_sliders_layout.addWidget(self.green_slider, 1, 1)
        
        self.green_spinbox = QSpinBox()
        self.green_spinbox.setRange(0, 255)
        self.green_spinbox.setValue(255)
        self.green_spinbox.valueChanged.connect(self.green_slider.setValue)
        self.green_spinbox.setEnabled(False)
        rgb_sliders_layout.addWidget(self.green_spinbox, 1, 2)
        
        # Blue
        rgb_sliders_layout.addWidget(QLabel("Blue:"), 2, 0)
        self.blue_slider = QSlider(Qt.Horizontal)
        self.blue_slider.setRange(0, 255)
        self.blue_slider.setValue(255)
        self.blue_slider.valueChanged.connect(self.on_rgb_changed)
        self.blue_slider.setEnabled(False)
        rgb_sliders_layout.addWidget(self.blue_slider, 2, 1)
        
        self.blue_spinbox = QSpinBox()
        self.blue_spinbox.setRange(0, 255)
        self.blue_spinbox.setValue(255)
        self.blue_spinbox.valueChanged.connect(self.blue_slider.setValue)
        self.blue_spinbox.setEnabled(False)
        rgb_sliders_layout.addWidget(self.blue_spinbox, 2, 2)
        
        # Connect spinboxes to sliders
        self.red_slider.valueChanged.connect(self.red_spinbox.setValue)
        self.green_slider.valueChanged.connect(self.green_spinbox.setValue)
        self.blue_slider.valueChanged.connect(self.blue_spinbox.setValue)
        
        rgb_layout.addLayout(rgb_sliders_layout)
        control_layout.addWidget(rgb_group)
        
        # Color temperature control
        temp_group = QGroupBox("Color Temperature")
        temp_layout = QVBoxLayout(temp_group)
        
        temp_controls = QHBoxLayout()
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(1000, 8000)
        self.temp_slider.setValue(4000)
        self.temp_slider.valueChanged.connect(self.on_color_temp_changed)
        self.temp_slider.setEnabled(False)
        
        self.temp_spinbox = QSpinBox()
        self.temp_spinbox.setRange(1000, 8000)
        self.temp_spinbox.setValue(4000)
        self.temp_spinbox.setSuffix("K")
        self.temp_spinbox.valueChanged.connect(self.temp_slider.setValue)
        self.temp_spinbox.setEnabled(False)
        
        self.temp_slider.valueChanged.connect(self.temp_spinbox.setValue)
        
        temp_controls.addWidget(QLabel("Temperature:"))
        temp_controls.addWidget(self.temp_slider)
        temp_controls.addWidget(self.temp_spinbox)
        temp_layout.addLayout(temp_controls)
        
        control_layout.addWidget(temp_group)
        
        # Speed control
        speed_group = QGroupBox("Animation Speed")
        speed_layout = QVBoxLayout(speed_group)
        
        speed_controls = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 100)
        self.speed_slider.setValue(50)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        self.speed_slider.setEnabled(False)
        
        self.speed_spinbox = QSpinBox()
        self.speed_spinbox.setRange(0, 100)
        self.speed_spinbox.setValue(50)
        self.speed_spinbox.setSuffix("%")
        self.speed_spinbox.valueChanged.connect(self.speed_slider.setValue)
        self.speed_spinbox.setEnabled(False)
        
        self.speed_slider.valueChanged.connect(self.speed_spinbox.setValue)
        
        speed_controls.addWidget(QLabel("Speed:"))
        speed_controls.addWidget(self.speed_slider)
        speed_controls.addWidget(self.speed_spinbox)
        speed_layout.addLayout(speed_controls)
        
        control_layout.addWidget(speed_group)
        
        control_layout.addStretch()
        self.tab_widget.addTab(control_widget, "Control")
    
    def create_scenes_tab(self):
        """Create the scenes selection tab"""
        scenes_widget = QWidget()
        scenes_layout = QVBoxLayout(scenes_widget)
        
        scenes_layout.addWidget(QLabel("Select a scene to apply to your light:"))
        
        # Create scrollable area for scenes
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)
        
        # Create scene buttons
        scenes = WizLightWrapper.get_scene_list()
        row, col = 0, 0
        for scene_id, scene_name in scenes.items():
            scene_btn = SceneButton(scene_id, scene_name)
            scene_btn.setStyleSheet("QRadiobutton")
            scene_btn.setIconSize(QSize(32, 32))
            scene_btn.setIcon(QIcon("resources/icons/scene_icon.png"))  # Placeholder icon
            # scene_btn.setFont(QFont("Lato", 10))
            scene_btn.setMinimumHeight(40)
            scene_btn.setToolTip(f"Set scene {scene_id}: {scene_name}")
            scene_btn.clicked.connect(lambda checked, sid=scene_id: self.set_scene(sid))
            scene_btn.setEnabled(False)
            scroll_layout.addWidget(scene_btn, row, col)
            
            col += 1
            if col >= 2:  # 2 columns
                col = 0
                row += 1
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scenes_layout.addWidget(scroll_area)
        
        # Store scene buttons for enabling/disabling
        self.scene_buttons = scroll_widget.findChildren(SceneButton)
        
        self.tab_widget.addTab(scenes_widget, "Scenes")
    
    def create_device_info_tab(self):
        """Create the device information tab"""
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        self.device_info_text = QTextEdit()
        self.device_info_text.setReadOnly(True)
        self.device_info_text.setPlainText("Select a device to view information")
        info_layout.addWidget(self.device_info_text)
        
        # Refresh button
        refresh_info_btn = QPushButton("Refresh Device Info")
        refresh_info_btn.clicked.connect(self.refresh_device_info)
        refresh_info_btn.setEnabled(False)
        self.refresh_info_btn = refresh_info_btn
        info_layout.addWidget(refresh_info_btn)
        
        self.tab_widget.addTab(info_widget, "Device Info")
    
    def setup_timers(self):
        """Setup timers for periodic updates"""
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.refresh_device_status)
        # Don't start automatically - only when device is selected
        
        # Initialize broadcast IP with auto-detected value
        self.auto_detect_broadcast()
    
    def auto_detect_broadcast(self):
        """Auto-detect and set the broadcast IP"""
        try:
            if self.wiz_wrapper:
                broadcast_ip = self.wiz_wrapper.get_default_broadcast_ip()
                self.broadcast_ip_input.setText(broadcast_ip)
                
                # Show network info in status bar
                network_info = self.wiz_wrapper.get_local_network_info()
                self.statusBar().showMessage(
                    f"Network: {network_info['local_ip']} -> {network_info['broadcast']}"
                )
        except Exception as e:
            self.broadcast_ip_input.setText("192.168.1.255")
            self.statusBar().showMessage("Using default broadcast IP")
    
    def discover_all_networks(self):
        """Discover devices on multiple networks"""
        self.discover_all_btn.setEnabled(False)
        self.discover_btn.setEnabled(False)
        self.discovery_progress.setVisible(True)
        self.discovery_progress.setRange(0, 0)  # Indeterminate progress
        self.statusBar().showMessage("Scanning all networks...")
        
        # Start multi-network discovery thread
        self.multi_discovery_thread = MultiNetworkDiscoveryThread()
        self.multi_discovery_thread.devices_found.connect(self.on_devices_discovered)
        self.multi_discovery_thread.error_occurred.connect(self.on_discovery_error)
        self.multi_discovery_thread.start()
    
    def discover_devices(self):
        """Start device discovery"""
        self.discover_btn.setEnabled(False)
        self.discovery_progress.setVisible(True)
        self.discovery_progress.setRange(0, 0)  # Indeterminate progress
        self.statusBar().showMessage("Discovering devices...")
        
        # Start discovery thread
        self.discovery_thread = DeviceDiscoveryThread(self.broadcast_ip_input.text())
        self.discovery_thread.devices_found.connect(self.on_devices_discovered)
        self.discovery_thread.error_occurred.connect(self.on_discovery_error)
        self.discovery_thread.start()
    
    def on_devices_discovered(self, devices):
        """Handle discovered devices"""
        self.devices = devices
        self.device_list.clear()
        
        for device in devices:
            item = QListWidgetItem(f"{device['ip']}")
            item.setData(Qt.UserRole, device)
            self.device_list.addItem(item)
        
        self.discover_btn.setEnabled(True)
        self.discovery_progress.setVisible(False)
        
        if devices:
            self.statusBar().showMessage(f"Found {len(devices)} device(s)")
        else:
            self.statusBar().showMessage("No devices found")
            QMessageBox.information(self, "Discovery", "No WizLight devices found on the network.")
    
    def on_discovery_error(self, error_msg):
        """Handle discovery error"""
        self.discover_btn.setEnabled(True)
        self.discover_all_btn.setEnabled(True)
        self.discovery_progress.setVisible(False)
        self.statusBar().showMessage("Discovery failed")
        QMessageBox.critical(self, "Discovery Error", f"Failed to discover devices:\n{error_msg}")
    
    def on_device_selected(self, item):
        """Handle device selection"""
        device = item.data(Qt.UserRole)
        self.current_device_ip = device['ip']
        self.current_device_label.setText(f"IP: {device['ip']}")
        
        # Enable controls
        self.enable_controls(True)
        
        # Start status updates
        self.status_timer.start(5000)  # Update every 5 seconds
        
        # Refresh device info
        self.refresh_device_status()
        self.refresh_device_info()
        
        self.statusBar().showMessage(f"Connected to device at {device['ip']}")
    
    def enable_controls(self, enabled: bool):
        """Enable or disable all control widgets"""
        controls = [
            self.on_btn, self.off_btn, self.brightness_slider, self.brightness_spinbox,
            self.red_slider, self.red_spinbox, self.green_slider, self.green_spinbox,
            self.blue_slider, self.blue_spinbox, self.temp_slider, self.temp_spinbox,
            self.speed_slider, self.speed_spinbox, self.color_picker_btn,
            self.refresh_status_btn, self.refresh_info_btn
        ]
        
        for control in controls:
            control.setEnabled(enabled)
        
        # Enable scene buttons
        for btn in self.scene_buttons:
            btn.setEnabled(enabled)
    
    def toggle_light(self, state: bool):
        """Toggle light on/off"""
        if not self.current_device_ip:
            return
        
        try:
            if state:
                self.wiz_wrapper.turn_on(self.current_device_ip)
                self.statusBar().showMessage("Light turned on")
            else:
                self.wiz_wrapper.turn_off(self.current_device_ip)
                self.statusBar().showMessage("Light turned off")
        except WizLightError as e:
            QMessageBox.critical(self, "Error", f"Failed to toggle light:\n{str(e)}")
    
    def on_brightness_changed(self, value):
        """Handle brightness change"""
        if not self.current_device_ip:
            return
        
        try:
            self.wiz_wrapper.set_brightness(self.current_device_ip, value)
            self.statusBar().showMessage(f"Brightness set to {value}%")
        except WizLightError as e:
            QMessageBox.critical(self, "Error", f"Failed to set brightness:\n{str(e)}")
    
    def on_rgb_changed(self):
        """Handle RGB color change"""
        if not self.current_device_ip:
            return
        
        r = self.red_slider.value()
        g = self.green_slider.value()
        b = self.blue_slider.value()
        
        # Update color preview
        self.color_preview.set_color(r, g, b)
        
        try:
            self.wiz_wrapper.set_rgb_color(self.current_device_ip, r, g, b)
            self.statusBar().showMessage(f"RGB color set to ({r}, {g}, {b})")
        except WizLightError as e:
            QMessageBox.critical(self, "Error", f"Failed to set RGB color:\n{str(e)}")
    
    def on_color_temp_changed(self, value):
        """Handle color temperature change"""
        if not self.current_device_ip:
            return
        
        try:
            self.wiz_wrapper.set_color_temperature(self.current_device_ip, value)
            self.statusBar().showMessage(f"Color temperature set to {value}K")
        except WizLightError as e:
            QMessageBox.critical(self, "Error", f"Failed to set color temperature:\n{str(e)}")
    
    def on_speed_changed(self, value):
        """Handle speed change"""
        if not self.current_device_ip:
            return
        
        try:
            self.wiz_wrapper.set_speed(self.current_device_ip, value)
            self.statusBar().showMessage(f"Speed set to {value}%")
        except WizLightError as e:
            QMessageBox.critical(self, "Error", f"Failed to set speed:\n{str(e)}")
    
    def open_color_picker(self):
        """Open color picker dialog"""
        current_color = QColor(
            self.red_slider.value(),
            self.green_slider.value(),
            self.blue_slider.value()
        )
        
        color = QColorDialog.getColor(current_color, self, "Choose Color")
        if color.isValid():
            self.red_slider.setValue(color.red())
            self.green_slider.setValue(color.green())
            self.blue_slider.setValue(color.blue())
    
    def create_credits_footer(self) -> QVBoxLayout:
        """Create the credits footer."""
        layout = QVBoxLayout()
        
        credits_label = QLabel(f'Created by <a href="{AppConfig.COMPANY_URL}" style="color: {AppConfig.BRAND_COLOR};">{AppConfig.COMPANY_NAME}</a>')
        credits_label.setOpenExternalLinks(True)
        credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_label.setStyleSheet("font-size: 12px; color: gray;")
        
        layout.addStretch()
        layout.addWidget(credits_label)
        layout.addStretch()
        
        return layout
    
    def set_scene(self, scene_id: int):
        """Set scene mode"""
        if not self.current_device_ip:
            return
        
        try:
            scene_name = WizLightWrapper.get_scene_list().get(scene_id, f"Scene {scene_id}")
            self.wiz_wrapper.set_scene(self.current_device_ip, scene_id)
            self.statusBar().showMessage(f"Scene set to {scene_name}")
        except WizLightError as e:
            QMessageBox.critical(self, "Error", f"Failed to set scene:\n{str(e)}")
    
    def refresh_device_status(self):
        """Refresh device status"""
        if not self.current_device_ip:
            return
        
        try:
            status = self.wiz_wrapper.get_status(self.current_device_ip)
            # Update UI based on status if available
            # This would depend on the actual status format returned by your device
            self.statusBar().showMessage("Status refreshed")
        except WizLightError as e:
            self.statusBar().showMessage("Failed to refresh status")
    
    def refresh_device_info(self):
        """Refresh device information"""
        if not self.current_device_ip:
            return
        
        try:
            device_info = self.wiz_wrapper.get_device_info(self.current_device_ip)
            
            # Format device info for display
            info_text = f"Device IP: {self.current_device_ip}\n\n"
            
            if isinstance(device_info, dict):
                for key, value in device_info.items():
                    info_text += f"{key}: {value}\n"
            else:
                info_text += str(device_info)
            
            self.device_info_text.setPlainText(info_text)
        except WizLightError as e:
            self.device_info_text.setPlainText(f"Failed to get device info:\n{str(e)}")
    
    def closeEvent(self, event):
        """Handle application close"""
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        if hasattr(self, 'discovery_thread') and self.discovery_thread.isRunning():
            self.discovery_thread.quit()
            self.discovery_thread.wait()
        
        event.accept()
