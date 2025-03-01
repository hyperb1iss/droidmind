"""
ADB Wrapper for DroidMind.

This module provides a wrapper around the adb_shell library to interact with Android devices.
"""

import os
import re
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.auth.keygen import keygen
from adb_shell.exceptions import (
    AdbCommandFailureException,
    AdbConnectionError,
    AdbTimeoutError,
)

from droidmind.utils import console


logger = logging.getLogger(__name__)


class ADBWrapper:
    """A wrapper around adb_shell to interact with Android devices."""

    def __init__(
        self,
        adb_key_path: Optional[str] = None,
        connection_timeout: float = 10.0,
        auth_timeout: float = 1.0,
    ):
        """Initialize the ADB wrapper.
        
        Args:
            adb_key_path: Path to the ADB key. If None, we'll use the default (~/.android/adbkey)
                          or generate one if it doesn't exist.
            connection_timeout: Timeout for connection to device in seconds.
            auth_timeout: Timeout for authentication in seconds.
        """
        self.connection_timeout = connection_timeout
        self.auth_timeout = auth_timeout
        self._devices: Dict[str, Union[AdbDeviceTcp, AdbDeviceUsb]] = {}
        
        # Set up ADB key
        self.adb_key_path = adb_key_path or self._get_default_adb_key_path()
        self._ensure_adb_key_exists()
        
        # Load signer
        self.signer = self._load_signer()
        
        console.info(f"ADB wrapper initialized with key: {self.adb_key_path}")

    def _get_default_adb_key_path(self) -> str:
        """Get the default path for the ADB key."""
        home = os.path.expanduser("~")
        return os.path.join(home, ".android", "adbkey")

    def _ensure_adb_key_exists(self) -> None:
        """Ensure ADB key exists, generate if it doesn't."""
        if not os.path.exists(self.adb_key_path):
            # Make sure directory exists
            key_dir = os.path.dirname(self.adb_key_path)
            if not os.path.exists(key_dir):
                os.makedirs(key_dir)
                
            console.info(f"Generating new ADB key at {self.adb_key_path}")
            try:
                keygen(self.adb_key_path)
            except Exception as e:
                console.error(f"Failed to generate ADB key: {e}")
                raise

    def _load_signer(self) -> PythonRSASigner:
        """Load the ADB key signer."""
        try:
            with open(self.adb_key_path, 'r') as f:
                private_key = f.read()
            with open(f"{self.adb_key_path}.pub", 'r') as f:
                public_key = f.read()
                
            return PythonRSASigner(public_key, private_key)
            
        except Exception as e:
            console.error(f"Failed to load ADB keys: {e}")
            raise
    
    async def connect_device_tcp(self, host: str, port: int = 5555) -> str:
        """Connect to a device over TCP/IP.
        
        Args:
            host: The IP address or hostname of the device.
            port: The port to connect to (default: 5555).
            
        Returns:
            The device serial number (IP:PORT).
        
        Raises:
            AdbConnectionError: If connection fails.
        """
        serial = f"{host}:{port}"
        
        if serial in self._devices:
            console.info(f"Device {serial} already connected")
            return serial
            
        device = AdbDeviceTcp(host, port, default_transport_timeout_s=self.connection_timeout)
        
        try:
            console.info(f"Connecting to {serial}...")
            await asyncio.to_thread(
                device.connect,
                rsa_keys=[self.signer],
                auth_timeout_s=self.auth_timeout
            )
            
            self._devices[serial] = device
            console.success(f"Connected to {serial}")
            return serial
            
        except AdbConnectionError as e:
            console.error(f"Failed to connect to {serial}: {e}")
            raise
            
    async def connect_device_usb(self) -> Optional[str]:
        """Connect to a USB device.
        
        Returns:
            The device serial number or None if no device found.
            
        Raises:
            AdbConnectionError: If connection fails.
        """
        device = AdbDeviceUsb(default_transport_timeout_s=self.connection_timeout)
        
        try:
            # Get USB device info first
            device_info = await asyncio.to_thread(device.get_serial_number)
            serial = device_info
            
            if serial in self._devices:
                console.info(f"Device {serial} already connected")
                return serial
                
            console.info(f"Connecting to USB device {serial}...")
            await asyncio.to_thread(
                device.connect,
                rsa_keys=[self.signer],
                auth_timeout_s=self.auth_timeout
            )
            
            self._devices[serial] = device
            console.success(f"Connected to USB device {serial}")
            return serial
            
        except Exception as e:
            console.error(f"Failed to connect to USB device: {e}")
            return None
    
    async def disconnect_device(self, serial: str) -> bool:
        """Disconnect from a device.
        
        Args:
            serial: The device serial number.
            
        Returns:
            True if disconnected, False if device wasn't connected.
        """
        if serial not in self._devices:
            console.warning(f"Device {serial} not connected")
            return False
            
        try:
            device = self._devices[serial]
            await asyncio.to_thread(device.close)
            del self._devices[serial]
            console.success(f"Disconnected from {serial}")
            return True
            
        except Exception as e:
            console.error(f"Error disconnecting from {serial}: {e}")
            return False
    
    async def get_devices(self) -> List[Dict[str, str]]:
        """Get a list of connected devices.
        
        Returns:
            A list of dictionaries containing device information.
        """
        result = []
        
        for serial, device in self._devices.items():
            try:
                # Check if device is still connected
                if not device.available:
                    console.warning(f"Device {serial} no longer available")
                    continue
                    
                # Get basic device info
                device_info = {
                    "serial": serial,
                    "status": "device",  # We only track connected devices
                }
                
                # Get model if possible
                try:
                    model = await self.get_device_property(serial, "ro.product.model")
                    if model:
                        device_info["model"] = model
                except Exception:
                    pass
                
                # Get Android version if possible
                try:
                    android_version = await self.get_device_property(serial, "ro.build.version.release")
                    if android_version:
                        device_info["android_version"] = android_version
                except Exception:
                    pass
                
                result.append(device_info)
                
            except Exception as e:
                console.error(f"Error getting info for device {serial}: {e}")
        
        return result
    
    async def shell(self, serial: str, command: str) -> str:
        """Run a shell command on the device.
        
        Args:
            serial: The device serial number.
            command: The shell command to run.
            
        Returns:
            The command output as a string.
            
        Raises:
            ValueError: If device is not connected.
            AdbCommandFailureException: If command execution fails.
        """
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")
            
        device = self._devices[serial]
        
        try:
            console.debug(f"Running shell command on {serial}: {command}")
            result = await asyncio.to_thread(device.shell, command)
            return result
            
        except AdbCommandFailureException as e:
            console.error(f"Command failed on {serial}: {e}")
            raise
            
        except Exception as e:
            console.error(f"Error executing command on {serial}: {e}")
            raise
    
    async def get_device_properties(self, serial: str) -> Dict[str, str]:
        """Get all properties from a device.
        
        Args:
            serial: The device serial number.
            
        Returns:
            Dictionary of device properties.
            
        Raises:
            ValueError: If device is not connected.
        """
        result = await self.shell(serial, "getprop")
        
        # Parse the getprop output into a dictionary
        properties = {}
        for line in result.splitlines():
            match = re.match(r'\[(.+?)\]: \[(.+?)\]', line)
            if match:
                key, value = match.groups()
                properties[key] = value
                
        return properties
    
    async def get_device_property(self, serial: str, prop_name: str) -> Optional[str]:
        """Get a specific property from a device.
        
        Args:
            serial: The device serial number.
            prop_name: The property name to get.
            
        Returns:
            The property value or None if not found.
            
        Raises:
            ValueError: If device is not connected.
        """
        try:
            result = await self.shell(serial, f"getprop {prop_name}")
            return result.strip() if result else None
        except Exception as e:
            console.error(f"Error getting property {prop_name} from {serial}: {e}")
            return None
    
    async def install_app(
        self, 
        serial: str, 
        apk_path: str, 
        reinstall: bool = False,
        grant_permissions: bool = True
    ) -> str:
        """Install an APK on the device.
        
        Args:
            serial: The device serial number.
            apk_path: Path to the APK file.
            reinstall: Whether to reinstall if app already exists.
            grant_permissions: Whether to automatically grant permissions.
            
        Returns:
            Installation result message.
            
        Raises:
            ValueError: If device is not connected or APK doesn't exist.
        """
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")
            
        if not os.path.exists(apk_path):
            raise ValueError(f"APK file not found: {apk_path}")
            
        # Build install command
        cmd = ["pm", "install"]
        if reinstall:
            cmd.append("-r")
        if grant_permissions:
            cmd.append("-g")
        cmd.append(f'"{apk_path}"')
        
        # Execute installation command
        result = await self.shell(serial, " ".join(cmd))
        
        if "Success" in result:
            return f"Successfully installed {os.path.basename(apk_path)}"
        else:
            return f"Installation failed: {result}"
    
    async def push_file(self, serial: str, local_path: str, device_path: str) -> str:
        """Push a file to the device.
        
        Args:
            serial: The device serial number.
            local_path: Path to the local file.
            device_path: Destination path on the device.
            
        Returns:
            Result message.
            
        Raises:
            ValueError: If device is not connected or local file doesn't exist.
        """
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")
            
        if not os.path.exists(local_path):
            raise ValueError(f"Local file not found: {local_path}")
            
        device = self._devices[serial]
        
        try:
            # Read file content
            with open(local_path, 'rb') as f:
                data = f.read()
                
            # Push to device
            console.info(f"Pushing {local_path} to {device_path} on {serial}")
            await asyncio.to_thread(device.push, local_path, device_path)
            
            return f"Successfully pushed {os.path.basename(local_path)} to {device_path}"
            
        except Exception as e:
            console.error(f"Error pushing file to {serial}: {e}")
            raise
    
    async def pull_file(self, serial: str, device_path: str, local_path: str) -> str:
        """Pull a file from the device.
        
        Args:
            serial: The device serial number.
            device_path: Path to the file on the device.
            local_path: Destination path on the local machine.
            
        Returns:
            Result message.
            
        Raises:
            ValueError: If device is not connected.
        """
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")
            
        device = self._devices[serial]
        
        try:
            # Create directory if it doesn't exist
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)
                
            # Pull from device
            console.info(f"Pulling {device_path} from {serial} to {local_path}")
            await asyncio.to_thread(device.pull, device_path, local_path)
            
            return f"Successfully pulled {device_path} to {os.path.basename(local_path)}"
            
        except Exception as e:
            console.error(f"Error pulling file from {serial}: {e}")
            raise
    
    async def reboot_device(self, serial: str, mode: str = "normal") -> str:
        """Reboot the device.
        
        Args:
            serial: The device serial number.
            mode: Reboot mode - "normal", "recovery", or "bootloader".
            
        Returns:
            Result message.
            
        Raises:
            ValueError: If device is not connected or mode is invalid.
        """
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")
            
        valid_modes = ["normal", "recovery", "bootloader"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid reboot mode. Must be one of: {', '.join(valid_modes)}")
            
        device = self._devices[serial]
        
        try:
            console.info(f"Rebooting {serial} into {mode} mode")
            
            if mode == "normal":
                await asyncio.to_thread(device.reboot)
            else:
                await asyncio.to_thread(device.shell, f"reboot {mode}")
                
            # Device will disconnect after reboot
            if serial in self._devices:
                del self._devices[serial]
                
            return f"Device {serial} rebooting into {mode} mode"
            
        except Exception as e:
            console.error(f"Error rebooting {serial}: {e}")
            raise
    
    async def capture_screenshot(self, serial: str, local_path: Optional[str] = None) -> str:
        """Capture a screenshot from the device.
        
        Args:
            serial: The device serial number.
            local_path: Path to save the screenshot (optional).
            
        Returns:
            Path to the saved screenshot.
            
        Raises:
            ValueError: If device is not connected.
        """
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")
            
        # Generate default path if not provided
        if not local_path:
            timestamp = asyncio.get_event_loop().time()
            local_path = f"screenshot_{serial.replace(':', '_')}_{int(timestamp)}.png"
            
        # Temp path on device
        device_path = "/sdcard/screenshot.png"
        
        try:
            # Take screenshot on device
            console.info(f"Taking screenshot on {serial}")
            await self.shell(serial, "screencap -p " + device_path)
            
            # Pull screenshot to local machine
            await self.pull_file(serial, device_path, local_path)
            
            # Clean up on device
            await self.shell(serial, f"rm {device_path}")
            
            return local_path
            
        except Exception as e:
            console.error(f"Error capturing screenshot from {serial}: {e}")
            raise
    
    async def list_apps(self, serial: str, system_apps: bool = False) -> List[Dict[str, str]]:
        """List installed apps on the device.
        
        Args:
            serial: The device serial number.
            system_apps: Whether to include system apps.
            
        Returns:
            List of dictionaries with app information.
            
        Raises:
            ValueError: If device is not connected.
        """
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")
            
        flags = "-3" if not system_apps else ""
        result = await self.shell(serial, f"pm list packages {flags} -f")
        
        apps = []
        for line in result.splitlines():
            if not line.startswith("package:"):
                continue
                
            # Parse package info
            # Format: package:/data/app/com.example.app-hash=.../base.apk=com.example.app
            parts = line[8:].split("=")
            if len(parts) < 2:
                continue
                
            apk_path = parts[0]
            package_name = parts[-1]
            
            # Get app label if possible
            try:
                label_result = await self.shell(
                    serial, 
                    f"dumpsys package {package_name} | grep \"applicationInfo\" | grep \"labelRes\""
                )
                label = "Unknown"
                if label_result:
                    label_match = re.search(r'label=(.*?)\s', label_result)
                    if label_match:
                        label = label_match.group(1)
            except Exception:
                label = "Unknown"
                
            apps.append({
                "package": package_name,
                "path": apk_path,
                "label": label,
            })
            
        return apps 