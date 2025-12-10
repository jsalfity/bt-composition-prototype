"""
Tests for behavior tree nodes.

These tests verify node instantiation and basic properties.
Note: Full functionality tests require ROS connection.
"""

import sys
import os
import unittest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import py_trees
from py_trees_nodes.primitives import (
    GoToPose,
    SetPen,
    PenUp,
    PenDown,
    MoveDistance,
    GetPose,
    CheckBounds,
)
from py_trees_nodes.composites import DrawShape, PatrolWaypoints


class TestPrimitiveNodes(unittest.TestCase):
    """Test primitive action nodes."""

    def test_goto_pose_creation(self):
        """Test GoToPose node can be created."""
        node = GoToPose(name="Test", x=5.0, y=5.0, theta=0.0)
        self.assertIsNotNone(node)
        self.assertEqual(node.name, "Test")
        self.assertEqual(node.target_x, 5.0)
        self.assertEqual(node.target_y, 5.0)

    def test_set_pen_creation(self):
        """Test SetPen node can be created."""
        node = SetPen(name="Test", r=255, g=0, b=0, width=3)
        self.assertIsNotNone(node)
        self.assertEqual(node.name, "Test")
        self.assertEqual(node.r, 255)
        self.assertEqual(node.g, 0)
        self.assertEqual(node.b, 0)

    def test_pen_up_creation(self):
        """Test PenUp convenience node."""
        node = PenUp(name="Test")
        self.assertIsNotNone(node)
        self.assertEqual(node.off, 1)  # Should disable drawing

    def test_pen_down_creation(self):
        """Test PenDown convenience node."""
        node = PenDown(name="Test", r=0, g=255, b=0)
        self.assertIsNotNone(node)
        self.assertEqual(node.off, 0)  # Should enable drawing
        self.assertEqual(node.g, 255)

    def test_move_distance_creation(self):
        """Test MoveDistance node."""
        node = MoveDistance(name="Test", distance=2.0, speed=1.0)
        self.assertIsNotNone(node)
        self.assertEqual(node.distance, 2.0)
        self.assertEqual(node.speed, 1.0)

    def test_get_pose_creation(self):
        """Test GetPose sensing node."""
        node = GetPose(name="Test", blackboard_key="test_pose")
        self.assertIsNotNone(node)
        self.assertEqual(node.blackboard_key, "test_pose")

    def test_check_bounds_creation(self):
        """Test CheckBounds condition node."""
        node = CheckBounds(name="Test", min_x=1.0, max_x=10.0)
        self.assertIsNotNone(node)
        self.assertEqual(node.min_x, 1.0)
        self.assertEqual(node.max_x, 10.0)

    def test_color_clamping(self):
        """Test that SetPen clamps color values."""
        node = SetPen(name="Test", r=300, g=-10, b=128)
        self.assertEqual(node.r, 255)  # Clamped to max
        self.assertEqual(node.g, 0)  # Clamped to min
        self.assertEqual(node.b, 128)  # Within range


class TestCompositionalNodes(unittest.TestCase):
    """Test compositional action nodes."""

    def test_draw_shape_circle(self):
        """Test DrawShape for circle."""
        node = DrawShape(
            name="Test", shape_type="circle", size=2.0, center_x=5.5, center_y=5.5
        )
        self.assertIsNotNone(node)
        self.assertIsInstance(node, py_trees.composites.Sequence)
        self.assertGreater(len(node.children), 0)

    def test_draw_shape_square(self):
        """Test DrawShape for square."""
        node = DrawShape(name="Test", shape_type="square", size=2.0)
        self.assertIsNotNone(node)
        self.assertGreater(len(node.children), 0)

    def test_draw_shape_triangle(self):
        """Test DrawShape for triangle."""
        node = DrawShape(name="Test", shape_type="triangle", size=2.0)
        self.assertIsNotNone(node)
        self.assertGreater(len(node.children), 0)

    def test_draw_shape_invalid_type(self):
        """Test DrawShape with invalid shape type."""
        with self.assertRaises(ValueError):
            DrawShape(name="Test", shape_type="pentagon", size=2.0)  # Not supported

    def test_patrol_waypoints_basic(self):
        """Test PatrolWaypoints with basic waypoints."""
        waypoints = [(3.0, 3.0), (8.0, 3.0), (8.0, 8.0)]
        node = PatrolWaypoints(name="Test", waypoints=waypoints)
        self.assertIsNotNone(node)
        self.assertIsInstance(node, py_trees.composites.Sequence)
        # Should have one GoToPose per waypoint
        self.assertEqual(len(node.children), len(waypoints))

    def test_patrol_waypoints_with_loop(self):
        """Test PatrolWaypoints with loop enabled."""
        waypoints = [(3.0, 3.0), (8.0, 3.0), (8.0, 8.0)]
        node = PatrolWaypoints(name="Test", waypoints=waypoints, loop=True)
        # Should have one extra node to return to start
        self.assertEqual(len(node.children), len(waypoints) + 1)

    def test_patrol_waypoints_with_theta(self):
        """Test PatrolWaypoints with orientation."""
        waypoints = [(3.0, 3.0, 0.0), (8.0, 3.0, 1.57)]
        node = PatrolWaypoints(name="Test", waypoints=waypoints)
        self.assertIsNotNone(node)
        self.assertEqual(len(node.children), len(waypoints))

    def test_patrol_waypoints_empty(self):
        """Test PatrolWaypoints with empty waypoints raises error."""
        with self.assertRaises(ValueError):
            PatrolWaypoints(name="Test", waypoints=[])


class TestNodeInheritance(unittest.TestCase):
    """Test that nodes properly inherit from base classes."""

    def test_primitive_nodes_inherit_base(self):
        """Test primitive nodes inherit from BaseActionNode."""
        from py_trees_nodes.base_action import BaseActionNode

        nodes = [
            GoToPose(name="Test", x=5.0, y=5.0),
            SetPen(name="Test"),
            MoveDistance(name="Test", distance=2.0),
        ]

        for node in nodes:
            self.assertIsInstance(node, BaseActionNode)

    def test_sensing_nodes_inherit_base(self):
        """Test sensing nodes inherit from SensingNode."""
        from py_trees_nodes.base_action import SensingNode

        nodes = [
            GetPose(name="Test"),
            CheckBounds(name="Test"),
        ]

        for node in nodes:
            self.assertIsInstance(node, SensingNode)

    def test_all_nodes_are_behaviors(self):
        """Test all nodes inherit from py_trees Behaviour."""
        nodes = [
            GoToPose(name="Test", x=5.0, y=5.0),
            SetPen(name="Test"),
            MoveDistance(name="Test", distance=2.0),
            GetPose(name="Test"),
            CheckBounds(name="Test"),
        ]

        for node in nodes:
            self.assertIsInstance(node, py_trees.behaviour.Behaviour)


if __name__ == "__main__":
    unittest.main()
