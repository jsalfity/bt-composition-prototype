"""
CheckBounds sensing node - Checks if the turtle is within specified bounds.

This node reads the turtle's position and returns SUCCESS if within bounds,
FAILURE otherwise.
"""

import py_trees
from roslibpy import Topic
from typing import Optional
from ..base_action import SensingNode


class CheckBounds(SensingNode):
    """
    Check if the turtle is within specified bounds.

    Returns SUCCESS if the turtle is within the bounds, FAILURE otherwise.
    This can be used for safety checks or as conditions in the behavior tree.

    Args:
        min_x: Minimum x coordinate (default: 1.0)
        max_x: Maximum x coordinate (default: 10.0)
        min_y: Minimum y coordinate (default: 1.0)
        max_y: Maximum y coordinate (default: 10.0)
        host: ROS host
        port: ROS port
    """

    def __init__(
        self,
        name: str = "CheckBounds",
        min_x: float = 1.0,
        max_x: float = 10.0,
        min_y: float = 1.0,
        max_y: float = 10.0,
        host: str = "localhost",
        port: int = 9090,
    ):
        super().__init__(name, host, port)
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

        self.pose_sub: Optional[Topic] = None
        self.current_x = 5.5  # Default turtlesim spawn position
        self.current_y = 5.5
        self.pose_received = False

    def setup(self, **kwargs):
        """Set up ROS topics."""
        if not super().setup(**kwargs):
            return False

        try:
            # Subscriber for current pose
            self.pose_sub = Topic(self.ros, "/turtle1/pose", "turtlesim/Pose")
            self.pose_sub.subscribe(self._pose_callback)

            self.logger.info(
                f"CheckBounds setup complete "
                f"(x:[{self.min_x},{self.max_x}], y:[{self.min_y},{self.max_y}])"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to set up CheckBounds: {e}")
            return False

    def _pose_callback(self, message):
        """Callback to update current pose."""
        self.current_x = message["x"]
        self.current_y = message["y"]
        self.pose_received = True

    def initialise(self):
        """Initialize when first ticked."""
        super().initialise()
        self.pose_received = False

    def update(self) -> py_trees.common.Status:
        """
        Update the behavior - check if within bounds.

        Returns:
            SUCCESS: Turtle is within bounds
            FAILURE: Turtle is outside bounds or ROS not connected
            RUNNING: Waiting for pose data
        """
        if not self.ros_connected:
            return py_trees.common.Status.FAILURE

        if not self.pose_received:
            # Still waiting for pose data
            return py_trees.common.Status.RUNNING

        # Check bounds
        in_bounds = (
            self.min_x <= self.current_x <= self.max_x
            and self.min_y <= self.current_y <= self.max_y
        )

        if in_bounds:
            self.logger.info(
                f"Turtle in bounds: ({self.current_x:.2f}, {self.current_y:.2f})"
            )
            return py_trees.common.Status.SUCCESS
        else:
            self.logger.warning(
                f"Turtle out of bounds: ({self.current_x:.2f}, {self.current_y:.2f})"
            )
            return py_trees.common.Status.FAILURE
