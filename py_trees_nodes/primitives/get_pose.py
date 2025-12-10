"""
GetPose sensing node - Retrieves the current pose of the turtle.

This node reads the turtle's current position and stores it for access by other nodes.
"""

import py_trees
from roslibpy import Topic
from typing import Optional, Dict
from ..base_action import SensingNode


class GetPose(SensingNode):
    """
    Retrieve the current pose of the turtle.

    This node subscribes to /turtle1/pose and stores the current position
    in the blackboard for other nodes to access.

    The pose is stored under the key specified by 'blackboard_key'.

    Args:
        blackboard_key: Key to store the pose in the blackboard (default: 'current_pose')
        host: ROS host
        port: ROS port
    """

    def __init__(
        self,
        name: str = "GetPose",
        blackboard_key: str = "current_pose",
        host: str = "localhost",
        port: int = 9090,
    ):
        super().__init__(name, host, port)
        self.blackboard_key = blackboard_key

        self.pose_sub: Optional[Topic] = None
        self.current_pose: Optional[Dict] = None
        self.pose_received = False

    def setup(self, **kwargs):
        """Set up ROS topics and blackboard."""
        if not super().setup(**kwargs):
            return False

        try:
            # Subscriber for current pose
            self.pose_sub = Topic(self.ros, "/turtle1/pose", "turtlesim/Pose")
            self.pose_sub.subscribe(self._pose_callback)

            # Set up blackboard
            self.blackboard = py_trees.blackboard.Client(name=self.name)
            self.blackboard.register_key(
                key=self.blackboard_key, access=py_trees.common.Access.WRITE
            )

            self.logger.info(
                f"GetPose setup complete (blackboard_key={self.blackboard_key})"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to set up GetPose: {e}")
            return False

    def _pose_callback(self, message):
        """Callback to receive pose updates."""
        self.current_pose = {
            "x": message["x"],
            "y": message["y"],
            "theta": message["theta"],
            "linear_velocity": message.get("linear_velocity", 0.0),
            "angular_velocity": message.get("angular_velocity", 0.0),
        }
        self.pose_received = True

    def initialise(self):
        """Initialize when first ticked."""
        super().initialise()
        self.pose_received = False

    def update(self) -> py_trees.common.Status:
        """
        Update the behavior - read current pose.

        Returns:
            SUCCESS: Pose read and stored in blackboard
            RUNNING: Waiting for pose data
            FAILURE: ROS not connected
        """
        if not self.ros_connected:
            return py_trees.common.Status.FAILURE

        if self.pose_received and self.current_pose:
            # Store pose in blackboard
            self.blackboard.set(self.blackboard_key, self.current_pose)
            self.logger.info(
                f"Pose retrieved: x={self.current_pose['x']:.2f}, "
                f"y={self.current_pose['y']:.2f}, "
                f"theta={self.current_pose['theta']:.2f}"
            )
            return py_trees.common.Status.SUCCESS

        # Still waiting for pose data
        return py_trees.common.Status.RUNNING
