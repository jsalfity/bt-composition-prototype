#!/usr/bin/env python3
"""
Behavior tree execution script.

This script loads and executes a behavior tree from a Python file.

Usage:
    python execution/run_bt.py path/to/behavior_tree.py

The BT file must define a create_root() function that returns the root node.
"""

import os
import sys
import importlib.util
import time
import logging
import uuid
import py_trees
from typing import Dict, Optional

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from execution.ros_connection import check_ros_connection


# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("BTExecutor")


def load_bt_module(bt_file_path: str):
    """
    Load a BT Python module from a file path.

    Args:
        bt_file_path: Path to the BT Python file

    Returns:
        The loaded module, or None if loading failed
    """
    if not os.path.exists(bt_file_path):
        logger.error(f"BT file not found: {bt_file_path}")
        return None

    if not bt_file_path.endswith(".py"):
        logger.error(f"BT file must be a Python file (.py): {bt_file_path}")
        return None

    try:
        # Load the module
        module_name = os.path.splitext(os.path.basename(bt_file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, bt_file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        logger.info(f"Successfully loaded BT module: {module_name}")
        return module

    except Exception as e:
        logger.error(f"Failed to load BT module: {e}")
        import traceback

        traceback.print_exc()
        return None


def setup_behavior_tree(root: py_trees.behaviour.Behaviour) -> bool:
    """
    Set up all nodes in the behavior tree.

    Args:
        root: The root node of the behavior tree

    Returns:
        True if setup successful, False otherwise
    """
    try:
        logger.info("Setting up behavior tree nodes...")

        # Get all nodes in the tree
        nodes = [root] + [child for child in root.iterate()]

        # Setup each node
        for node in nodes:
            if hasattr(node, "setup"):
                result = node.setup()
                if result is False:
                    logger.error(f"Failed to setup node: {node.name}")
                    return False

        logger.info("Behavior tree setup complete")
        return True

    except Exception as e:
        logger.error(f"Error during behavior tree setup: {e}")
        import traceback

        traceback.print_exc()
        return False


def build_node_lookup(
    root: py_trees.behaviour.Behaviour,
) -> Dict[uuid.UUID, py_trees.behaviour.Behaviour]:
    """
    Build a lookup table from behaviour id to behaviour instance.

    This lets us resolve SnapshotVisitor ids back to readable node names.
    """
    nodes = [root] + [child for child in root.iterate()]
    return {node.id: node for node in nodes}


def print_tick_visualization(
    tick_count: int,
    root: py_trees.behaviour.Behaviour,
    snapshot: py_trees.visitors.SnapshotVisitor,
    node_lookup: Dict[uuid.UUID, py_trees.behaviour.Behaviour],
) -> None:
    """
    Pretty-print the nodes ticked this cycle and their statuses.
    """
    ticked_names = [
        node_lookup[node_id].name for node_id in snapshot.visited.keys() if node_id in node_lookup
    ]
    running_names = [
        node_lookup[node_id].name
        for node_id, status in snapshot.visited.items()
        if status == py_trees.common.Status.RUNNING and node_id in node_lookup
    ]

    print("\n" + "-" * 80)
    print(f"TICK {tick_count:03d} | Root status: {root.status}")
    if ticked_names:
        print("Tick path: " + " -> ".join(ticked_names))
    else:
        print("Tick path: (no nodes visited)")

    if running_names:
        print("Running: " + ", ".join(running_names))

    print(
        py_trees.display.unicode_tree(
            root,
            show_status=True,
            show_only_visited=True,
            visited=snapshot.visited,
            previously_visited=snapshot.previously_visited,
        )
    )
    print("-" * 80 + "\n")


def execute_behavior_tree(
    root: py_trees.behaviour.Behaviour,
    tick_rate: float = 10.0,
    max_ticks: int = 1000
):
    """
    Execute the behavior tree.

    Args:
        root: The root node of the behavior tree
        tick_rate: Ticks per second (Hz)
        max_ticks: Maximum number of ticks before timeout

    Returns:
        True if execution completed successfully, False otherwise
    """
    try:
        logger.info("Starting behavior tree execution...")
        logger.info(f"Tick rate: {tick_rate} Hz, Max ticks: {max_ticks}")

        # Display initial tree structure
        print("\n" + "=" * 80)
        print("BEHAVIOR TREE STRUCTURE")
        print("=" * 80)
        print(py_trees.display.unicode_tree(root, show_status=True))
        print("=" * 80 + "\n")

        # Create the behavior tree
        tree = py_trees.trees.BehaviourTree(root)
        snapshot_visitor = py_trees.visitors.SnapshotVisitor()
        tree.visitors.append(snapshot_visitor)
        node_lookup = build_node_lookup(root)

        tick_period = 1.0 / tick_rate
        tick_count = 0
        last_status = None

        while tick_count < max_ticks:
            # Tick the tree
            tree.tick()
            tick_count += 1
            print_tick_visualization(tick_count, root, snapshot_visitor, node_lookup)

            # Check status
            current_status = root.status

            # Log status changes
            if current_status != last_status:
                logger.info(f"Tick {tick_count}: Root status = {current_status}")
                last_status = current_status

                # Print tree state on status change
                print("\n" + "=" * 80)
                print(f"TICK {tick_count}: Tree Status = {current_status}")
                print("=" * 80)
                print(py_trees.display.unicode_tree(root, show_status=True))
                print("=" * 80 + "\n")

            # Check if tree is done
            if current_status == py_trees.common.Status.SUCCESS:
                logger.info(
                    f"Behavior tree completed successfully after {tick_count} ticks"
                )
                print("\n" + "=" * 80)
                print("FINAL TREE STATE")
                print("=" * 80)
                print(py_trees.display.unicode_tree(root, show_status=True))
                print("=" * 80 + "\n")
                return True

            elif current_status == py_trees.common.Status.FAILURE:
                logger.error(f"Behavior tree failed after {tick_count} ticks")
                print("\n" + "=" * 80)
                print("FINAL TREE STATE (FAILED)")
                print("=" * 80)
                print(py_trees.display.unicode_tree(root, show_status=True))
                print("=" * 80 + "\n")
                return False

            # Sleep until next tick
            time.sleep(tick_period)

        # Timeout
        logger.warning(f"Behavior tree execution timed out after {max_ticks} ticks")
        print("\n" + "=" * 80)
        print("FINAL TREE STATE (TIMEOUT)")
        print("=" * 80)
        print(py_trees.display.unicode_tree(root, show_status=True))
        print("=" * 80 + "\n")
        return False

    except KeyboardInterrupt:
        logger.info("Execution interrupted by user")
        return False

    except Exception as e:
        logger.error(f"Error during behavior tree execution: {e}")
        import traceback

        traceback.print_exc()
        return False


def shutdown_behavior_tree(root: py_trees.behaviour.Behaviour):
    """
    Shutdown all nodes in the behavior tree.

    Args:
        root: The root node of the behavior tree
    """
    try:
        logger.info("Shutting down behavior tree nodes...")

        # Get all nodes in the tree
        nodes = [root] + [child for child in root.iterate()]

        # Shutdown each node
        for node in nodes:
            if hasattr(node, "shutdown"):
                try:
                    node.shutdown()
                except Exception as e:
                    logger.warning(f"Error shutting down node {node.name}: {e}")

        logger.info("Behavior tree shutdown complete")

    except Exception as e:
        logger.error(f"Error during behavior tree shutdown: {e}")


def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python execution/run_bt.py path/to/behavior_tree.py")
        print("\nExamples:")
        print("    python execution/run_bt.py bt_library/manual_examples/draw_square.py")
        sys.exit(1)

    bt_file_path = sys.argv[1]

    # Skip initial ROS check - nodes will handle connection
    # (Avoids Twisted reactor restart issue)
    logger.info("Will connect to ROS when setting up nodes...")

    # Load the BT module
    module = load_bt_module(bt_file_path)
    if module is None:
        sys.exit(1)

    # Check for create_root function
    if not hasattr(module, "create_root"):
        logger.error("BT module must define a create_root() function")
        sys.exit(1)

    # Create the behavior tree root
    try:
        root = module.create_root()
        logger.info(f"Created behavior tree root: {root.name}")
    except Exception as e:
        logger.error(f"Failed to create behavior tree root: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Setup the behavior tree
    if not setup_behavior_tree(root):
        logger.error("Failed to setup behavior tree")
        sys.exit(1)

    # Execute the behavior tree
    success = execute_behavior_tree(root, tick_rate=10.0, max_ticks=1000)

    # Shutdown
    shutdown_behavior_tree(root)

    # Exit with appropriate code
    if success:
        logger.info("Execution completed successfully")
        sys.exit(0)
    else:
        logger.error("Execution failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
