"""
ROS connection management utilities.

Provides helper functions for managing roslibpy connections to rosbridge.
"""

from roslibpy import Ros
import logging
from typing import Optional


class ROSConnectionManager:
    """
    Manages a single ROS connection via rosbridge.

    This class provides a singleton-like pattern for managing the ROS connection,
    ensuring that only one connection is maintained across all nodes.
    """

    _instance: Optional["ROSConnectionManager"] = None
    _ros: Optional[Ros] = None
    _connected: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host: str = "localhost", port: int = 9090):
        """Initialize the connection manager (only once)."""
        if not hasattr(self, "initialized"):
            self.host = host
            self.port = port
            self.logger = logging.getLogger("ROSConnectionManager")
            self.initialized = True

    def connect(self, host: str = "localhost", port: int = 9090) -> bool:
        """
        Connect to rosbridge.

        Args:
            host: The rosbridge host
            port: The rosbridge port

        Returns:
            True if connection successful, False otherwise
        """
        if self._connected and self._ros:
            self.logger.info("Already connected to ROS")
            return True

        try:
            self.logger.info(f"Connecting to ROS at {host}:{port}...")
            self._ros = Ros(host=host, port=port)
            self._ros.run()
            self._connected = True
            self.host = host
            self.port = port
            self.logger.info("Successfully connected to ROS")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to ROS: {e}")
            self._connected = False
            return False

    def disconnect(self):
        """Disconnect from rosbridge."""
        if self._ros and self._connected:
            try:
                self._ros.terminate()
                self._connected = False
                self.logger.info("Disconnected from ROS")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}")

    def get_ros(self) -> Optional[Ros]:
        """
        Get the ROS connection instance.

        Returns:
            The Ros instance if connected, None otherwise
        """
        return self._ros if self._connected else None

    def is_connected(self) -> bool:
        """Check if currently connected to ROS."""
        return self._connected

    @classmethod
    def reset(cls):
        """Reset the singleton instance (useful for testing)."""
        if cls._instance:
            cls._instance.disconnect()
        cls._instance = None
        cls._ros = None
        cls._connected = False


def check_ros_connection(host: str = "localhost", port: int = 9090) -> bool:
    """
    Check if ROS is accessible via rosbridge.

    Args:
        host: The rosbridge host
        port: The rosbridge port

    Returns:
        True if ROS is accessible, False otherwise
    """
    try:
        ros = Ros(host=host, port=port)
        ros.run()

        # Wait a moment for connection
        import time

        time.sleep(0.5)

        is_connected = ros.is_connected
        ros.terminate()

        return is_connected

    except Exception as e:
        logging.error(f"Failed to check ROS connection: {e}")
        return False
