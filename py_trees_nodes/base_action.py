"""
Base action node class for py_trees behaviors that communicate with ROS via roslibpy.

This module provides the foundation for all behavior tree action nodes in the system.
"""

import py_trees
from roslibpy import Ros, Topic, Service
from typing import Optional
import logging


class BaseActionNode(py_trees.behaviour.Behaviour):
    """
    Base class for all ROS action nodes in the behavior tree.

    This class handles the connection to ROS via roslibpy (rosbridge websocket)
    and provides common functionality for all action nodes.

    Attributes:
        ros: The roslibpy Ros connection instance
        ros_connected: Boolean indicating if connected to ROS
    """

    # Shared ROS connection across all nodes
    _shared_ros: Optional[Ros] = None
    _ros_running = False

    def __init__(self, name: str, host: str = "localhost", port: int = 9090):
        """
        Initialize the base action node.

        Args:
            name: The name of this behavior node
            host: The rosbridge host (default: localhost)
            port: The rosbridge port (default: 9090)
        """
        super().__init__(name)
        self.host = host
        self.port = port
        self.ros: Optional[Ros] = None
        self.ros_connected = False
        self.logger = logging.getLogger(name)

    def setup(self, **kwargs):
        """
        Set up the ROS connection and any topics/services.

        This is called once when the behavior tree is initialized.
        Subclasses should override this to set up their specific topics/services,
        but should call super().setup() first.
        """
        try:
            # Use shared ROS connection if available
            if BaseActionNode._shared_ros is None:
                BaseActionNode._shared_ros = Ros(host=self.host, port=self.port)

            self.ros = BaseActionNode._shared_ros

            # Only run reactor once
            if not BaseActionNode._ros_running:
                self.ros.run()
                BaseActionNode._ros_running = True
                self.logger.info(f"Started ROS connection at {self.host}:{self.port}")

            self.ros_connected = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to ROS: {e}")
            self.ros_connected = False
            return False

    def initialise(self):
        """
        Initialize the behavior when it is first ticked.

        This is called every time the behavior transitions from an idle state
        to being ticked. Subclasses should override this for behavior-specific
        initialization.
        """
        if not self.ros_connected:
            self.logger.warning(f"{self.name}: Not connected to ROS")

    def update(self) -> py_trees.common.Status:
        """
        Update method called when the behavior is ticked.

        This must be overridden by subclasses to implement the actual behavior logic.

        Returns:
            Status: SUCCESS, FAILURE, or RUNNING
        """
        if not self.ros_connected:
            self.logger.error(f"{self.name}: Cannot update - not connected to ROS")
            return py_trees.common.Status.FAILURE

        # Subclasses must override this
        raise NotImplementedError("Subclasses must implement update()")

    def terminate(self, new_status: py_trees.common.Status):
        """
        Terminate the behavior.

        This is called when the behavior either finishes successfully, fails,
        or is interrupted. Subclasses can override this for cleanup.

        Args:
            new_status: The status the behavior is transitioning to
        """
        pass

    def shutdown(self):
        """
        Shutdown the ROS connection.

        This should be called when the behavior tree is shutting down.
        """
        if self.ros and self.ros_connected:
            try:
                self.ros.terminate()
                self.ros_connected = False
                self.logger.info(f"Disconnected from ROS")
            except Exception as e:
                self.logger.error(f"Error during shutdown: {e}")


class SensingNode(BaseActionNode):
    """
    Base class for sensing/condition checking nodes.

    These nodes typically check conditions and return SUCCESS or FAILURE
    without modifying the environment.
    """

    def __init__(self, name: str, host: str = "localhost", port: int = 9090):
        super().__init__(name, host, port)
