"""
Python wrapper for wizlightcpp C++ executable
Provides a clean Python API for controlling Wiz lights
"""

import subprocess
import json
import re
import os
import sys
import socket
import ipaddress
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class WizLightError(Exception):
    """Custom exception for WizLight operations"""
    pass


class WizLightWrapper:
    """Python wrapper for the wizlightcpp C++ executable"""
    
    def __init__(self, executable_path: Optional[str] = None):
        """
        Initialize the wrapper
        
        Args:
            executable_path: Path to wizlightcpp executable. If None, looks in the ../build/ directory.
        """
        try:
            # This is the path when running from a PyInstaller bundle
            base_path = sys._MEIPASS
        except Exception:
            # This is the path when running in a normal Python environment
            base_path = os.path.abspath(".")

        wizlightcpp_path = os.path.join(base_path, 'wizlightcpp')
        
        if os.path.exists(wizlightcpp_path):
            executable_path = wizlightcpp_path

        if executable_path is None:
            # Look for the executable in the build directory
            current_dir = Path(__file__).parent
            self.executable_path = current_dir.parent / "build" / "wizlightcpp"
        else:
            self.executable_path = Path(executable_path)
        
        if not self.executable_path.exists():
            raise WizLightError(f"wizlightcpp executable not found at {self.executable_path}")
    
    def _run_command(self, args: List[str]) -> str:
        """
        Run a wizlightcpp command and return the output
        
        Args:
            args: Command arguments
            
        Returns:
            Command output as string
            
        Raises:
            WizLightError: If command fails
        """
        try:
            cmd = [str(self.executable_path)] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise WizLightError(f"Command failed: {result.stderr}")
            
            return result.stdout.strip()
        
        except subprocess.TimeoutExpired:
            raise WizLightError("Command timed out")
        except Exception as e:
            raise WizLightError(f"Failed to execute command: {str(e)}")
    
    def discover_devices(self, broadcast_ip: str = "192.168.1.255") -> List[Dict]:
        """
        Discover Wiz devices on the network
        
        Args:
            broadcast_ip: Broadcast IP address for discovery
            
        Returns:
            List of discovered devices with their information
        """
        try:
            output = self._run_command(["discover", "--bcast", broadcast_ip])
            
            # Parse the JSON response
            devices = []
            
            try:
                # Try to parse as JSON first (the correct format)
                response_data = json.loads(output)
                
                # Handle the JSON structure from wizlightcpp
                if "bulb_response" in response_data:
                    bulb_data = response_data["bulb_response"]
                    devices.append({
                        'ip': bulb_data.get('ip'),
                        'mac': bulb_data.get('mac'),
                        'devMac': bulb_data.get('devMac'),
                        'moduleName': bulb_data.get('moduleName'),
                        'raw_response': output
                    })
                
            except json.JSONDecodeError:
                # Fallback to regex parsing for older format or non-JSON output
                lines = output.split('\n')
                
                for line in lines:
                    if 'ip' in line.lower() and 'mac' in line.lower():
                        # Try to extract IP and MAC from the response
                        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match:
                            devices.append({
                                'ip': ip_match.group(1),
                                'raw_response': line
                            })
            
            return devices
        
        except Exception as e:
            raise WizLightError(f"Discovery failed: {str(e)}")
    
    def get_default_broadcast_ip(self) -> str:
        """
        Auto-detect the most likely broadcast IP for the current network
        
        Returns:
            Broadcast IP address as string
        """
        try:
            # Get the local IP address by connecting to a remote address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Calculate broadcast address for /24 network (most common)
            network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            return str(network.broadcast_address)
        except Exception:
            # Fallback to common default
            return "192.168.1.255"
    
    def discover_devices_multi_network(self) -> List[Dict]:
        """
        Try discovery on multiple common network ranges
        
        Returns:
            List of discovered devices from all networks
        """
        # Get auto-detected broadcast first, then try common ones
        auto_broadcast = self.get_default_broadcast_ip()
        
        common_broadcasts = [
            auto_broadcast,        # Auto-detected (most likely to work)
            "192.168.1.255",     # Most common home network
            "192.168.0.255",     # Another common range  
            "10.0.0.255",        # Some corporate networks
            "172.16.255.255",    # Private network range
            "192.168.2.255",     # Alternative home range
            "192.168.10.255"     # Some router defaults
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_broadcasts = []
        for broadcast in common_broadcasts:
            if broadcast not in seen:
                unique_broadcasts.append(broadcast)
                seen.add(broadcast)
        
        all_devices = []
        for broadcast_ip in unique_broadcasts:
            try:
                devices = self.discover_devices(broadcast_ip)
                all_devices.extend(devices)
            except WizLightError:
                continue  # Try next broadcast address
        
        # Remove duplicate devices based on IP address
        unique_devices = []
        seen_ips = set()
        for device in all_devices:
            device_ip = device.get('ip')
            if device_ip and device_ip not in seen_ips:
                unique_devices.append(device)
                seen_ips.add(device_ip)
        
        return unique_devices
    
    def validate_broadcast_ip(self, ip: str) -> bool:
        """
        Validate that the IP address is a valid broadcast address
        
        Args:
            ip: IP address to validate
            
        Returns:
            True if valid broadcast IP, False otherwise
        """
        try:
            addr = ipaddress.IPv4Address(ip)
            # Simple check: broadcast addresses typically end in .255
            # More sophisticated validation could check if it's actually a broadcast for a network
            return str(addr).endswith('.255')
        except (ipaddress.AddressValueError, ValueError):
            return False
    
    def get_local_network_info(self) -> Dict[str, str]:
        """
        Get information about the local network
        
        Returns:
            Dictionary with local IP, network, and broadcast information
        """
        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Calculate network info for /24 (most common)
            network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            
            return {
                'local_ip': local_ip,
                'network': str(network),
                'broadcast': str(network.broadcast_address),
                'netmask': str(network.netmask)
            }
        except Exception:
            return {
                'local_ip': 'Unknown',
                'network': 'Unknown',
                'broadcast': '192.168.1.255',
                'netmask': '255.255.255.0'
            }
    
    def turn_on(self, ip: str) -> bool:
        """Turn on the light"""
        try:
            self._run_command(["on", "--ip", ip])
            return True
        except Exception as e:
            raise WizLightError(f"Failed to turn on light: {str(e)}")
    
    def turn_off(self, ip: str) -> bool:
        """Turn off the light"""
        try:
            self._run_command(["off", "--ip", ip])
            return True
        except Exception as e:
            raise WizLightError(f"Failed to turn off light: {str(e)}")
    
    def get_status(self, ip: str) -> Dict:
        """Get the current status of the light"""
        try:
            output = self._run_command(["status", "--ip", ip])
            
            # Try to parse JSON response
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                # If not JSON, return raw output
                return {"raw_status": output}
        
        except Exception as e:
            raise WizLightError(f"Failed to get status: {str(e)}")
    
    def get_device_info(self, ip: str) -> Dict:
        """Get device information"""
        try:
            output = self._run_command(["getdeviceinfo", "--ip", ip])
            
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return {"raw_info": output}
        
        except Exception as e:
            raise WizLightError(f"Failed to get device info: {str(e)}")
    
    def set_brightness(self, ip: str, brightness: int) -> bool:
        """
        Set brightness level
        
        Args:
            ip: Device IP address
            brightness: Brightness level (0-100)
        """
        if not 0 <= brightness <= 100:
            raise WizLightError("Brightness must be between 0 and 100")
        
        try:
            self._run_command(["setbrightness", "--ip", ip, "--dim", str(brightness)])
            return True
        except Exception as e:
            raise WizLightError(f"Failed to set brightness: {str(e)}")
    
    def set_rgb_color(self, ip: str, r: int, g: int, b: int) -> bool:
        """
        Set RGB color
        
        Args:
            ip: Device IP address
            r, g, b: RGB values (0-255)
        """
        for val, name in [(r, 'red'), (g, 'green'), (b, 'blue')]:
            if not 0 <= val <= 255:
                raise WizLightError(f"{name} value must be between 0 and 255")
        
        try:
            self._run_command([
                "setrgbcolor", "--ip", ip,
                "--r", str(r), "--g", str(g), "--b", str(b)
            ])
            return True
        except Exception as e:
            raise WizLightError(f"Failed to set RGB color: {str(e)}")
    
    def set_color_temperature(self, ip: str, temp: int) -> bool:
        """
        Set color temperature
        
        Args:
            ip: Device IP address
            temp: Color temperature in Kelvin (1000-8000)
        """
        if not 1000 <= temp <= 8000:
            raise WizLightError("Color temperature must be between 1000 and 8000 Kelvin")
        
        try:
            self._run_command(["setcolortemp", "--ip", ip, "--temp", str(temp)])
            return True
        except Exception as e:
            raise WizLightError(f"Failed to set color temperature: {str(e)}")
    
    def set_scene(self, ip: str, scene_id: int) -> bool:
        """
        Set scene mode
        
        Args:
            ip: Device IP address
            scene_id: Scene ID (1-32)
        """
        if not 1 <= scene_id <= 32:
            raise WizLightError("Scene ID must be between 1 and 32")
        
        try:
            self._run_command(["setscene", "--ip", ip, "--scene", str(scene_id)])
            return True
        except Exception as e:
            raise WizLightError(f"Failed to set scene: {str(e)}")
    
    def set_speed(self, ip: str, speed: int) -> bool:
        """
        Set color changing speed
        
        Args:
            ip: Device IP address
            speed: Speed percentage (0-100)
        """
        if not 0 <= speed <= 100:
            raise WizLightError("Speed must be between 0 and 100")
        
        try:
            self._run_command(["setspeed", "--ip", ip, "--speed", str(speed)])
            return True
        except Exception as e:
            raise WizLightError(f"Failed to set speed: {str(e)}")
    
    def reboot_device(self, ip: str) -> bool:
        """Reboot the device"""
        try:
            self._run_command(["reboot", "--ip", ip])
            return True
        except Exception as e:
            raise WizLightError(f"Failed to reboot device: {str(e)}")
    
    @staticmethod
    def get_scene_list() -> Dict[int, str]:
        """Get the list of available scenes"""
        return {
            1: "Ocean",
            2: "Romance",
            3: "Sunset",
            4: "Party",
            5: "Fireplace",
            6: "Cozy",
            7: "Forest",
            8: "Pastel Colors",
            9: "Wake up",
            10: "Bedtime",
            11: "Warm White",
            12: "Daylight",
            13: "Cool white",
            14: "Night light",
            15: "Focus",
            16: "Relax",
            17: "True colors",
            18: "TV time",
            19: "Plantgrowth",
            20: "Spring",
            21: "Summer",
            22: "Fall",
            23: "Deepdive",
            24: "Jungle",
            25: "Mojito",
            26: "Club",
            27: "Christmas",
            28: "Halloween",
            29: "Candlelight",
            30: "Golden white",
            31: "Pulse",
            32: "Steampunk"
        }


# Example usage
if __name__ == "__main__":
    try:
        wiz = WizLightWrapper()
        
        # Discover devices
        print("Discovering devices...")
        devices = wiz.discover_devices()
        print(f"Found {len(devices)} devices:")
        for device in devices:
            print(f"  - {device['ip']}")
        
        if devices:
            ip = devices[0]['ip']
            print(f"\nTesting with device at {ip}")
            
            # Get status
            status = wiz.get_status(ip)
            print(f"Status: {status}")
            
            # Turn on
            wiz.turn_on(ip)
            print("Light turned on")
            
    except WizLightError as e:
        print(f"Error: {e}")
