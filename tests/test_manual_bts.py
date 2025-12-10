"""
Tests for manual behavior tree examples.

These tests verify that the manual BT examples can be loaded and have
the correct structure.
"""

import sys
import os
import unittest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import py_trees
from bt_library.manual_examples import draw_square, patrol_waypoints


class TestManualBTs(unittest.TestCase):
    """Test hand-crafted behavior tree examples."""

    def test_draw_square_loads(self):
        """Test that draw_square BT can be loaded."""
        root = draw_square.create_root()
        self.assertIsNotNone(root)
        self.assertIsInstance(root, py_trees.behaviour.Behaviour)

    def test_draw_square_structure(self):
        """Test draw_square has correct structure."""
        root = draw_square.create_root()

        # Should be a Sequence
        self.assertIsInstance(root, py_trees.composites.Sequence)

        # Should have children
        self.assertGreater(len(root.children), 0)

        # Should have SetPen and GoToPose nodes
        child_types = [type(child).__name__ for child in root.children]
        self.assertIn("SetPen", child_types)
        self.assertIn("GoToPose", child_types)

    def test_patrol_waypoints_loads(self):
        """Test that patrol_waypoints BT can be loaded."""
        root = patrol_waypoints.create_root()
        self.assertIsNotNone(root)
        self.assertIsInstance(root, py_trees.behaviour.Behaviour)

    def test_patrol_waypoints_structure(self):
        """Test patrol_waypoints has correct structure."""
        root = patrol_waypoints.create_root()

        # Should be a Sequence
        self.assertIsInstance(root, py_trees.composites.Sequence)

        # Should have children
        self.assertGreater(len(root.children), 0)

        # Should have GetPose, CheckBounds, and PatrolWaypoints nodes
        child_types = [type(child).__name__ for child in root.children]
        self.assertIn("GetPose", child_types)
        self.assertIn("CheckBounds", child_types)
        self.assertIn("PatrolWaypoints", child_types)

    def test_all_nodes_have_names(self):
        """Test that all nodes in manual BTs have names."""
        for bt_module in [draw_square, patrol_waypoints]:
            root = bt_module.create_root()

            # Check root has name
            self.assertTrue(hasattr(root, "name"))
            self.assertIsNotNone(root.name)

            # Check all children have names
            for child in root.iterate():
                self.assertTrue(hasattr(child, "name"))
                self.assertIsNotNone(child.name)


class TestBTValidation(unittest.TestCase):
    """Test validation of behavior tree files."""

    def test_draw_square_syntax_valid(self):
        """Test draw_square passes syntax validation."""
        from validation.syntax_checker import validate_bt_syntax

        bt_file = os.path.join(
            os.path.dirname(__file__), "../bt_library/manual_examples/draw_square.py"
        )

        is_valid, errors, warnings = validate_bt_syntax(bt_file)

        self.assertTrue(is_valid, f"Syntax errors: {errors}")

    def test_patrol_waypoints_syntax_valid(self):
        """Test patrol_waypoints passes syntax validation."""
        from validation.syntax_checker import validate_bt_syntax

        bt_file = os.path.join(
            os.path.dirname(__file__),
            "../bt_library/manual_examples/patrol_waypoints.py",
        )

        is_valid, errors, warnings = validate_bt_syntax(bt_file)

        self.assertTrue(is_valid, f"Syntax errors: {errors}")


if __name__ == "__main__":
    unittest.main()
