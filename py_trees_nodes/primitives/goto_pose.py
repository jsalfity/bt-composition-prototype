"""
GoToPose action node - Moves the turtle to a specified pose.

This node publishes velocity commands to move the turtle to the target position
and orientation.
"""

import py_trees
from roslibpy import Topic
import math
import time
from typing import Optional
from ..base_action import BaseActionNode


class GoToPose(BaseActionNode):
    """
    Move the turtle to a target pose (x, y, theta).

    This node uses a simple proportional controller to move the turtle to the
    target position and orientation. It publishes to /turtle1/cmd_vel.

    Args:
        x: Target x coordinate (0-11, turtlesim bounds)
        y: Target y coordinate (0-11, turtlesim bounds)
        theta: Target orientation in radians (optional, will only position if None)
        tolerance_pos: Position tolerance in meters (default: 0.1)
        tolerance_angle: Angular tolerance in radians (default: 0.1)
    """

    def __init__(
        self,
        name: str,
        x: float,
        y: float,
        theta: Optional[float] = None,
        tolerance_pos: float = 0.1,
        tolerance_angle: float = 0.1,
        host: str = "localhost",
        port: int = 9090,
    ):
        super().__init__(name, host, port)
        self.target_x = x
        self.target_y = y
        self.target_theta = theta
        self.tolerance_pos = tolerance_pos
        self.tolerance_angle = tolerance_angle

        self.cmd_vel_pub: Optional[Topic] = None
        self.pose_sub: Optional[Topic] = None

        # Current pose
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_theta = 0.0

        # Control parameters
        self.linear_speed_gain = 1.0
        self.angular_speed_gain = 2.0
        self.max_linear_speed = 2.0
        self.max_angular_speed = 2.0

    def setup(self, **kwargs):
        """Set up ROS topics for command and pose."""
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
                f"GoToPose setup complete for target ({self.target_x}, {self.target_y}, {self.target_theta})"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to set up topics: {e}")
            return False

    def _pose_callback(self, message):
        """Callback to update current pose from /turtle1/pose."""
        self.current_x = message["x"]
        self.current_y = message["y"]
        self.current_theta = message["theta"]

    def initialise(self):
        """Initialize when first ticked."""
        super().initialise()
        self.logger.info(
            f"Starting navigation to ({self.target_x}, {self.target_y}, {self.target_theta})"
        )

    def update(self) -> py_trees.common.Status:
        """
        Update the behavior - move toward target pose.

        Returns:
            RUNNING: Still moving to target
            SUCCESS: Reached target pose
            FAILURE: ROS not connected
        """
        if not self.ros_connected:
            return py_trees.common.Status.FAILURE

        # Calculate distance to target
        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y
        distance = math.sqrt(dx**2 + dy**2)

        # Check if we've reached the position target
        if distance < self.tolerance_pos:
            # Check if we need to align to a target angle
            if self.target_theta is not None:
                angle_error = self._normalize_angle(
                    self.target_theta - self.current_theta
                )

                if abs(angle_error) < self.tolerance_angle:
                    # Reached both position and orientation targets
                    self._stop_turtle()
                    self.logger.info(
                        f"Reached target pose ({self.target_x}, {self.target_y}, {self.target_theta})"
                    )
                    return py_trees.common.Status.SUCCESS
                else:
                    # Rotate to target angle
                    self._rotate_to_angle(angle_error)
                    return py_trees.common.Status.RUNNING
            else:
                # Only position target, no orientation requirement
                self._stop_turtle()
                self.logger.info(
                    f"Reached target position ({self.target_x}, {self.target_y})"
                )
                return py_trees.common.Status.SUCCESS

        # Calculate angle to target
        angle_to_target = math.atan2(dy, dx)
        angle_error = self._normalize_angle(angle_to_target - self.current_theta)

        # If we need to turn more than 90 degrees, just rotate first
        if abs(angle_error) > math.pi / 2:
            self._rotate_to_angle(angle_error)
        else:
            # Move forward while adjusting heading
            linear_vel = min(self.linear_speed_gain * distance, self.max_linear_speed)
            angular_vel = self.angular_speed_gain * angle_error
            angular_vel = max(
                min(angular_vel, self.max_angular_speed), -self.max_angular_speed
            )

            self._publish_velocity(linear_vel, angular_vel)

        return py_trees.common.Status.RUNNING

    def _normalize_angle(self, angle: float) -> float:
        """Normalize angle to [-pi, pi]."""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    def _rotate_to_angle(self, angle_error: float):
        """Rotate in place to correct angle error."""
        angular_vel = self.angular_speed_gain * angle_error
        angular_vel = max(
            min(angular_vel, self.max_angular_speed), -self.max_angular_speed
        )
        self._publish_velocity(0.0, angular_vel)

    def _publish_velocity(self, linear: float, angular: float):
        """Publish velocity command to turtle."""
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
