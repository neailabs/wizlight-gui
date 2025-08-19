# WizLight GUI Controller

A modern graphical user interface for controlling Wiz smart lights, built with PySide6 and Python. This GUI provides an intuitive interface for all the functionality available in the wizlightcpp command-line tool (<https://github.com/yachoukh/wizlightcpp>)

## Features

- **Device Discovery**: Automatically discover Wiz lights on your networks
- **Power Control**: Turn lights on/off with dedicated buttons
- **Brightness Control**: Adjust brightness with sliders and spinboxes
- **RGB Color Control**: Set custom colors with RGB sliders or color picker
- **Color Temperature**: Adjust white light temperature (1000K-8000K)
- **Scene Selection**: Choose from 32 built-in lighting scenes
- **Animation Speed**: Control the speed of dynamic scenes
- **Device Information**: View detailed device information
- **Real-time Updates**: Automatic status updates every 5 seconds

## Prerequisites

Before running this GUI, make sure you have:

1. **Built wizlightcpp**: The C++ executable should be compiled and available in the `../build/` directory (i.e. inside a folder called "build" in the parent directory of this project. For Mac users on M series macbooks, you can download this file from (<https://www.neailabs.com/download/1006/?tmstv=1755590204>))
2. **Python 3.8+**: Required for PySide6
3. **PySide6**: Qt6 bindings for Python

## Installation

1. **Install Python dependencies**:
   ```bash
   cd wizlight-gui
   pip install -r requirements.txt
   ```

2. **Ensure wizlightcpp is built**:
   ```bash
   cd ..  # Go back to project root
   mkdir build
   cd build
   cmake ..
   make
   ```

## Usage

### Running the GUI

```bash
cd wizlight-gui
python main.py
```

### Using the Interface

1. **Device Discovery**:
   - Enter your network's broadcast IP (default: 192.168.1.255)
   - Click "Discover Devices" to scan for Wiz lights
   - Select a device from the discovered list

2. **Control Your Lights**:
   - **Power**: Use the green "Turn On" and red "Turn Off" buttons
   - **Brightness**: Drag the slider or enter a value (0-100%)
   - **RGB Colors**: Use individual RGB sliders or click "Choose Color" for a color picker
   - **Color Temperature**: Adjust white light warmth (1000K-8000K)
   - **Scenes**: Switch to the "Scenes" tab and click any scene button
   - **Speed**: Control animation speed for dynamic scenes

3. **Device Information**:
   - Switch to the "Device Info" tab to view detailed device information
   - Click "Refresh Device Info" to update the information

### Network Configuration

- **Broadcast IP**: Usually your network IP with .255 at the end
  - For 192.168.1.x networks: use 192.168.1.255
  - For 192.168.0.x networks: use 192.168.0.255
  - For 10.0.0.x networks: use 10.0.0.255

## Available Scenes

The GUI includes all 32 built-in Wiz scenes:

1. Ocean
2. Romance
3. Sunset
4. Party
5. Fireplace
6. Cozy
7. Forest
8. Pastel Colors
9. Wake up
10. Bedtime
11. Warm White
12. Daylight
13. Cool white
14. Night light
15. Focus
16. Relax
17. True colors
18. TV time
19. Plantgrowth
20. Spring
21. Summer
22. Fall
23. Deepdive
24. Jungle
25. Mojito
26. Club
27. Christmas
28. Halloween
29. Candlelight
30. Golden white
31. Pulse
32. Steampunk

## New Features (v1.1)

### Enhanced Network Discovery
- **Auto-Detection**: Automatically detects your network's broadcast IP
- **Multi-Network Scanning**: "Scan All Networks" button tries multiple common network ranges
- **Network Information**: Shows current network details in the status bar
- **Flexible Configuration**: Works across different network configurations without hardcoding

### Improved User Experience
- **Auto** button next to broadcast IP field for one-click network detection
- **Scan All Networks** button for comprehensive device discovery
- **Better Error Handling**: More informative error messages and validation
- **Network Validation**: Validates broadcast IP addresses before use

## Troubleshooting

### Common Issues

1. **"wizlightcpp executable not found"**:
   - Make sure the C++ project is built in the `../build/` directory
   - Check that the executable has proper permissions

2. **No devices found during discovery**:
   - Try the "Auto" button to detect your network's broadcast IP automatically
   - Use "Scan All Networks" to try multiple network ranges
   - Verify your Wiz lights are connected to the same network
   - Check that your firewall isn't blocking UDP traffic

3. **Commands fail after selecting a device**:
   - Verify the device IP is reachable
   - Check that the Wiz light is powered on and connected
   - Try refreshing the device status

4. **GUI appears but controls don't work**:
   - Make sure you've selected a device from the discovered list
   - Controls are disabled until a device is selected

5. **Discovery worked in CLI but not in GUI** (Fixed in v1.1):
   - This issue has been resolved - the GUI now properly parses JSON responses from wizlightcpp
   - The Python wrapper now correctly handles the JSON format returned by the C++ executable

### Network Troubleshooting

- Test the command-line tool first: `../build/wizlightcpp discover --bcast YOUR_BROADCAST_IP`
- Verify network connectivity: `ping DEVICE_IP`
- Check if other devices can control the lights (official Wiz app)

## Architecture

The GUI consists of several components:

- **wizlight_wrapper.py**: Python wrapper around the C++ executable
- **main_window.py**: Main GUI window with all controls
- **main.py**: Application entry point
- **theme_manager.py**: Manages light/dark mode and stylesheet
- **resources/styles_(light/dark).qss**: Modern CSS-like styling for both light & dark modes

## macOS Specific Notes

- The GUI is designed to work well with macOS's native appearance
- Retina displays are supported as well as dark mode.
- The interface follows macOS design guidelines
- A build script for Macs is provided ("build_macos.py") if you want to create a MacOS Application bundle. You can do this
by running `python build_macos.py` from the project root. This will create the Mac app in the root directory, which you can then move to the "Applications" folder on your mac.

## Future Enhancements

- Windows and Linux optimizations
- Device favorites and presets
- Scheduling and automation
- Multiple device control
- Custom scene creation

## License

This GUI application follows the MIT license. Further details can be found in the `LICENSE` file.
