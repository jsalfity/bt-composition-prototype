"""
Manual example behavior tree: Patrol waypoints

This BT demonstrates:
- Using PatrolWaypoints compositional node
- Using GetPose to read current position
- Using CheckBounds as a safety check
- Using Selector for conditional behavior

The turtle will patrol between several waypoints with a bounds check.
"""

import py_trees
import sys
import os

# Add parent directory to path to import py_trees_nodes
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from py_trees_nodes.composites import PatrolWaypoints
from py_trees_nodes.primitives import GetPose, CheckBounds


def create_root() -> py_trees.behaviour.Behaviour:
    """
    Create the behavior tree for patrolling waypoints.

    The tree structure:
    - Sequence (main)
        - GetPose (read current position)
        - CheckBounds (ensure we're in safe area)
        - PatrolWaypoints (visit waypoints with loop)

    Returns:
        The root node of the behavior tree
    """

    # Create the main sequence
    root = py_trees.composites.Sequence(
        name="PatrolMission", memory=True  # Remember progress through children
    )

    # Get current pose (stores in blackboard)
    get_pose = GetPose(name="ReadStartPosition", blackboard_key="start_pose")

    # Check if we're in bounds (safety check)
    check_bounds = CheckBounds(
        name="SafetyBoundsCheck", min_x=1.0, max_x=10.0, min_y=1.0, max_y=10.0
    )

    # Define patrol waypoints (forming a rectangular path)
    waypoints = [
        (3.0, 3.0),  # Bottom-left corner
        (8.0, 3.0),  # Bottom-right corner
        (8.0, 8.0),  # Top-right corner
        (3.0, 8.0),  # Top-left corner
    ]

    # Create patrol behavior
    patrol = PatrolWaypoints(
        name="PatrolRectangle", waypoints=waypoints, loop=True  # Return to start
    )

    # Add all behaviors to the sequence
    root.add_children([get_pose, check_bounds, patrol])

    return root


if __name__ == "__main__":
    """
    Run this BT directly for testing.

    Usage:
        python bt_library/manual_examples/patrol_waypoints.py
    """
    print("Creating patrol_waypoints behavior tree...")
    root = create_root()

    print("Behavior tree created successfully!")
    print("\nTo execute this BT, use:")
    print(
        "    python execution/run_bt.py bt_library/manual_examples/patrol_waypoints.py"
    )

    # Display the tree structure
    print("\nTree structure:")
    print(py_trees.display.unicode_tree(root, show_status=True))
