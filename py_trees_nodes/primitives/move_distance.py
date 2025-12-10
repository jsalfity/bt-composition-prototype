"""
MoveDistance action node - Moves the turtle forward or backward by a specified distance.

This node publishes velocity commands to move the turtle a fixed distance.
"""

import py_trees
from roslibpy import Topic
import math
from typing import Optional
from ..base_action import BaseActionNode


class MoveDistance(BaseActionNode):
    """
    Move the turtle forward or backward by a specified distance.

    Args:
        distance: Distance to move in meters (positive = forward, negative = backward)
        speed: Linear speed (default: 1.0 m/s)
        host: ROS host
        port: ROS port
    """

    def __init__(
        self,
        name: str,
        distance: float,
        speed: float = 1.0,
        host: str = "localhost",
        port: int = 9090,
    ):
        super().__init__(name, host, port)
        self.distance = distance
        self.speed = abs(speed)  # Ensure positive

        self.cmd_vel_pub: Optional[Topic] = None
        self.pose_sub: Optional[Topic] = None

        # Current pose
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_theta = 0.0

        # Start position (recorded when movement begins)
        self.start_x = None
        self.start_y = None

    def setup(self, **kwargs):
        """Set up ROS topics."""
        if not super().setup(**kwargs):
            return False

        try:
            # Publisher for velocity commands
            self.cmd_vel_pub = Topic(
                self.ros, "/turtle1/cmd_vel", "geometry_msgs/Twist"
            )

            # Subscriber for current pose
            self.pose_sub = Topic(self.ros, "/turtle1/pose", "turtlesim/Pose")
            self.pose_sub.subscribe(self._pose_callback)

            self.logger.info(
                f"MoveDistance setup complete (distance={self.distance}, speed={self.speed})"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to set up topics: {e}")
            return False

    def _pose_callback(self, message):
        """Callback to update current pose."""
        self.current_x = message["x"]
        self.current_y = message["y"]
        self.current_theta = message["theta"]

    def initialise(self):
        """Initialize when first ticked - record start position."""
        super().initialise()
        self.start_x = self.current_x
        self.start_y = self.current_y
        self.logger.info(
            f"Starting to move {self.distance}m at {self.speed}m/s from ({self.start_x}, {self.start_y})"
        )

    def update(self) -> py_trees.common.Status:
        """
        Update the behavior - move the specified distance.

        Returns:
            RUNNING: Still moving
            SUCCESS: Completed the distance
            FAILURE: ROS not connected or no start position
        """
        if not self.ros_connected:
            return py_trees.common.Status.FAILURE

        if self.start_x is None or self.start_y is None:
            self.logger.error("Start position not recorded")
            return py_trees.common.Status.FAILURE

        # Calculate distance traveled
        dx = self.current_x - self.start_x
        dy = self.current_y - self.start_y
        distance_traveled = math.sqrt(dx**2 + dy**2)

        # Check if we've traveled the target distance
        if distance_traveled >= abs(self.distance):
            self._stop_turtle()
            self.logger.info(f"Completed movement of {distance_traveled:.2f}m")
            return py_trees.common.Status.SUCCESS

        # Continue moving
        linear_vel = self.speed if self.distance > 0 else -self.speed
        self._publish_velocity(linear_vel, 0.0)

        return py_trees.common.Status.RUNNING

    def _publish_velocity(self, linear: float, angular: float):
        """Publish velocity command."""
        if self.cmd_vel_pub:
            message = {
                "linear": {"x": linear, "y": 0.0, "z": 0.0},
                "angular": {"x": 0.0, "y": 0.0, "z": angular},
            }
            self.cmd_vel_pub.publish(message)

    def _stop_turtle(self):
        """Stop the turtle."""
        self._publish_velocity(0.0, 0.0)

    def terminate(self, new_status: py_trees.common.Status):
        """Stop the turtle when terminating."""
        self._stop_turtle()
        super().terminate(new_status)
