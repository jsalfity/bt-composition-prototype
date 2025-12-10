"""
DrawShape compositional node - Draws geometric shapes.

This node is a higher-level action that combines SetPen and GoToPose
to draw shapes like circles, squares, and triangles.
"""

import py_trees
import math
from typing import Tuple
from ..primitives import SetPen, GoToPose


class DrawShape(py_trees.composites.Sequence):
    """
    Draw a geometric shape (circle, square, or triangle).

    This is a compositional node that creates a sequence of SetPen and GoToPose
    actions to draw the specified shape.

    Args:
        shape_type: Type of shape ('circle', 'square', 'triangle')
        size: Size of the shape (radius for circle, side length for others)
        center_x: X coordinate of shape center (default: 5.5)
        center_y: Y coordinate of shape center (default: 5.5)
        color: RGB color tuple (r, g, b), values 0-255 (default: white)
        width: Pen width (default: 3)
        segments: Number of segments for circle (default: 36)
    """

    def __init__(
        self,
        name: str,
        shape_type: str,
        size: float,
        center_x: float = 5.5,
        center_y: float = 5.5,
        color: Tuple[int, int, int] = (255, 255, 255),
        width: int = 3,
        segments: int = 36,
        host: str = "localhost",
        port: int = 9090,
    ):
        super().__init__(name=name, memory=True)

        self.shape_type = shape_type.lower()
        self.size = size
        self.center_x = center_x
        self.center_y = center_y
        self.color = color
        self.width = width
        self.segments = segments
        self.host = host
        self.port = port

        # Build the shape
        self._build_shape()

    def _build_shape(self):
        """Build the behavior tree for drawing the shape."""

        # Set pen color
        set_pen = SetPen(
            name=f"SetPen_{self.shape_type}",
            r=self.color[0],
            g=self.color[1],
            b=self.color[2],
            width=self.width,
            off=0,  # Pen down
            host=self.host,
            port=self.port,
        )
        self.add_child(set_pen)

        # Generate waypoints based on shape type
        if self.shape_type == "circle":
            waypoints = self._generate_circle_waypoints()
        elif self.shape_type == "square":
            waypoints = self._generate_square_waypoints()
        elif self.shape_type == "triangle":
            waypoints = self._generate_triangle_waypoints()
        else:
            raise ValueError(f"Unknown shape type: {self.shape_type}")

        # Add GoToPose nodes for each waypoint
        for i, (x, y) in enumerate(waypoints):
            goto = GoToPose(
                name=f"{self.shape_type}_point_{i}",
                x=x,
                y=y,
                theta=None,  # Don't care about orientation
                host=self.host,
                port=self.port,
            )
            self.add_child(goto)

    def _generate_circle_waypoints(self):
        """Generate waypoints for a circle."""
        waypoints = []
        for i in range(self.segments + 1):  # +1 to close the circle
            angle = (2 * math.pi * i) / self.segments
            x = self.center_x + self.size * math.cos(angle)
            y = self.center_y + self.size * math.sin(angle)
            waypoints.append((x, y))
        return waypoints

    def _generate_square_waypoints(self):
        """Generate waypoints for a square."""
        half_size = self.size / 2
        waypoints = [
            (self.center_x - half_size, self.center_y - half_size),  # Bottom-left
            (self.center_x + half_size, self.center_y - half_size),  # Bottom-right
            (self.center_x + half_size, self.center_y + half_size),  # Top-right
            (self.center_x - half_size, self.center_y + half_size),  # Top-left
            (self.center_x - half_size, self.center_y - half_size),  # Back to start
        ]
        return waypoints

    def _generate_triangle_waypoints(self):
        """Generate waypoints for an equilateral triangle."""
        # Triangle with one vertex pointing up
        height = self.size * math.sqrt(3) / 2
        waypoints = [
            (self.center_x, self.center_y + 2 * height / 3),  # Top vertex
            (self.center_x - self.size / 2, self.center_y - height / 3),  # Bottom-left
            (self.center_x + self.size / 2, self.center_y - height / 3),  # Bottom-right
            (self.center_x, self.center_y + 2 * height / 3),  # Back to top
        ]
        return waypoints
