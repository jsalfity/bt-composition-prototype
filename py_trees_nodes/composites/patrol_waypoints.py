"""
PatrolWaypoints compositional node - Navigates through a list of waypoints.

This node creates a sequence of GoToPose actions to visit multiple waypoints.
"""

import py_trees
from typing import List, Tuple
from ..primitives import GoToPose


class PatrolWaypoints(py_trees.composites.Sequence):
    """
    Navigate through a list of waypoints in order.

    This is a compositional node that creates a sequence of GoToPose actions.
    Optionally, it can loop back to the first waypoint at the end.

    Args:
        waypoints: List of (x, y) or (x, y, theta) tuples representing waypoints
        loop: If True, add a final waypoint back to the start (default: False)
        host: ROS host
        port: ROS port
    """

    def __init__(
        self,
        name: str,
        waypoints: List[Tuple],
        loop: bool = False,
        host: str = "localhost",
        port: int = 9090,
    ):
        super().__init__(name=name, memory=True)

        if not waypoints:
            raise ValueError("Waypoints list cannot be empty")

        self.waypoints = waypoints
        self.loop = loop
        self.host = host
        self.port = port

        # Build the patrol sequence
        self._build_patrol()

    def _build_patrol(self):
        """Build the behavior tree for patrolling waypoints."""

        # Add all waypoints
        for i, waypoint in enumerate(self.waypoints):
            # Parse waypoint tuple
            if len(waypoint) == 2:
                x, y = waypoint
                theta = None
            elif len(waypoint) == 3:
                x, y, theta = waypoint
            else:
                raise ValueError(
                    f"Invalid waypoint format: {waypoint}. Must be (x,y) or (x,y,theta)"
                )

            # Create GoToPose node
            goto = GoToPose(
                name=f"Waypoint_{i}",
                x=x,
                y=y,
                theta=theta,
                host=self.host,
                port=self.port,
            )
            self.add_child(goto)

        # If loop, add first waypoint at the end
        if self.loop and len(self.waypoints) > 0:
            first_waypoint = self.waypoints[0]

            if len(first_waypoint) == 2:
                x, y = first_waypoint
                theta = None
            else:
                x, y, theta = first_waypoint

            goto_loop = GoToPose(
                name="Return_to_start",
                x=x,
                y=y,
                theta=theta,
                host=self.host,
                port=self.port,
            )
            self.add_child(goto_loop)
