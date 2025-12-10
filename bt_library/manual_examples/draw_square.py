"""
Manual example behavior tree: Draw a square

This BT demonstrates:
- Using SetPen to configure drawing color
- Using a Sequence to execute multiple actions in order
- Using GoToPose to navigate to waypoints

The turtle will draw a blue square with 2-unit sides.
"""

import py_trees
import sys
import os

# Add parent directory to path to import py_trees_nodes
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from py_trees_nodes.primitives import GoToPose, SetPen


def create_root() -> py_trees.behaviour.Behaviour:
    """
    Create the behavior tree for drawing a square.

    The tree structure:
    - Sequence (draw square)
        - SetPen (blue, width=3)
        - GoToPose (3, 3)    # Start corner
        - GoToPose (5, 3)    # Move right
        - GoToPose (5, 5)    # Move up
        - GoToPose (3, 5)    # Move left
        - GoToPose (3, 3)    # Back to start (completes square)

    Returns:
        The root node of the behavior tree
    """

    # Create the sequence that will execute all actions in order
    root = py_trees.composites.Sequence(
        name="DrawSquare", memory=True  # Remember progress through children
    )

    # Configure the pen: blue color, medium width
    set_pen = SetPen(
        name="SetPenRed", r=255, g=0, b=0, width=3, off=0  # Pen down (drawing enabled)
    )

    # Define the square corners (2x2 square starting at (3,3))
    corner1 = GoToPose(name="Corner1", x=3.0, y=3.0, theta=0.0)
    corner2 = GoToPose(name="Corner2_Right", x=5.0, y=3.0, theta=0.0)
    corner3 = GoToPose(name="Corner3_Up", x=5.0, y=5.0, theta=0.0)
    corner4 = GoToPose(name="Corner4_Left", x=3.0, y=5.0, theta=0.0)
    corner5 = GoToPose(
        name="Corner5_Close", x=3.0, y=3.0, theta=0.0
    )  # Close the square

    # Add all actions to the sequence
    root.add_children([set_pen, corner1, corner2, corner3, corner4, corner5])

    return root


if __name__ == "__main__":
    """
    Run this BT directly for testing.

    Usage:
        python bt_library/manual_examples/draw_square.py
    """
    print("Creating draw_square behavior tree...")
    root = create_root()

    # For direct execution, you would need to:
    # 1. Set up all nodes (call setup())
    # 2. Create a BehaviourTree
    # 3. Tick the tree until completion

    print("Behavior tree created successfully!")
    print("\nTo execute this BT, use:")
    print("    python execution/run_bt.py bt_library/manual_examples/draw_square.py")

    # Display the tree structure
    print("\nTree structure:")
    print(py_trees.display.unicode_tree(root, show_status=True))
