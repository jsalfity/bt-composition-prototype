#!/usr/bin/env python3
"""
Quick verification script to check project setup.

This script verifies that:
- All modules can be imported
- Manual BT examples can be loaded
- Validation tools work
- Basic node creation works

Does NOT require ROS connection.
"""

import sys
import os

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_status(message, status):
    """Print a status message with color."""
    if status == "pass":
        print(f"  {GREEN}✓{RESET} {message}")
    elif status == "fail":
        print(f"  {RED}✗{RESET} {message}")
    elif status == "warn":
        print(f"  {YELLOW}⚠{RESET} {message}")
    else:
        print(f"  {message}")


def check_imports():
    """Check that all modules can be imported."""
    print("\n1. Checking imports...")

    checks = [
        ("py_trees", lambda: __import__("py_trees")),
        ("roslibpy", lambda: __import__("roslibpy")),
        ("yaml", lambda: __import__("yaml")),
        ("py_trees_nodes", lambda: __import__("py_trees_nodes")),
        ("validation", lambda: __import__("validation")),
        ("execution", lambda: __import__("execution")),
    ]

    all_passed = True
    for name, import_func in checks:
        try:
            import_func()
            print_status(f"Import {name}", "pass")
        except Exception as e:
            print_status(f"Import {name}: {e}", "fail")
            all_passed = False

    return all_passed


def check_nodes():
    """Check that action nodes can be created."""
    print("\n2. Checking action nodes...")

    try:
        from py_trees_nodes.primitives import (
            GoToPose,
            SetPen,
            MoveDistance,
            GetPose,
            CheckBounds,
        )
        from py_trees_nodes.composites import DrawShape, PatrolWaypoints

        # Try creating each node
        nodes = [
            ("GoToPose", lambda: GoToPose(name="Test", x=5.0, y=5.0)),
            ("SetPen", lambda: SetPen(name="Test", r=255, g=0, b=0)),
            ("MoveDistance", lambda: MoveDistance(name="Test", distance=2.0)),
            ("GetPose", lambda: GetPose(name="Test")),
            ("CheckBounds", lambda: CheckBounds(name="Test")),
            (
                "DrawShape",
                lambda: DrawShape(name="Test", shape_type="circle", size=2.0),
            ),
            (
                "PatrolWaypoints",
                lambda: PatrolWaypoints(name="Test", waypoints=[(3, 3), (8, 8)]),
            ),
        ]

        all_passed = True
        for name, create_func in nodes:
            try:
                node = create_func()
                print_status(f"Create {name}", "pass")
            except Exception as e:
                print_status(f"Create {name}: {e}", "fail")
                all_passed = False

        return all_passed

    except Exception as e:
        print_status(f"Failed to import nodes: {e}", "fail")
        return False


def check_manual_bts():
    """Check that manual BT examples can be loaded."""
    print("\n3. Checking manual behavior trees...")

    try:
        from bt_library.manual_examples import draw_square, patrol_waypoints

        examples = [
            ("draw_square", draw_square),
            ("patrol_waypoints", patrol_waypoints),
        ]

        all_passed = True
        for name, module in examples:
            try:
                root = module.create_root()
                if root is None:
                    raise ValueError("create_root() returned None")
                print_status(f"Load {name}", "pass")
            except Exception as e:
                print_status(f"Load {name}: {e}", "fail")
                all_passed = False

        return all_passed

    except Exception as e:
        print_status(f"Failed to import manual BTs: {e}", "fail")
        return False


def check_validation():
    """Check that validation tools work."""
    print("\n4. Checking validation tools...")

    try:
        from validation import validate_bt_syntax, validate_bt_ros

        # Test on draw_square example
        test_file = "bt_library/manual_examples/draw_square.py"

        try:
            is_valid, errors, warnings = validate_bt_syntax(test_file)
            if is_valid:
                print_status("Syntax validation", "pass")
            else:
                print_status(f"Syntax validation: {errors}", "fail")
                return False
        except Exception as e:
            print_status(f"Syntax validation: {e}", "fail")
            return False

        try:
            is_valid, errors, warnings = validate_bt_ros(test_file, check_live=False)
            if is_valid:
                print_status("ROS validation", "pass")
            else:
                print_status(f"ROS validation: {errors}", "fail")
                return False
        except Exception as e:
            print_status(f"ROS validation: {e}", "fail")
            return False

        return True

    except Exception as e:
        print_status(f"Failed to import validation: {e}", "fail")
        return False


def check_skill_files():
    """Check that project-level files exist and are readable."""
    print("\n5. Checking project files...")

    files = [
        "action_library/action_library.yaml",
    ]

    all_passed = True
    for file_path in files:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if len(content) > 100:  # Reasonable size check
                    print_status(f"Read {file_path}", "pass")
                else:
                    print_status(f"File too small: {file_path}", "warn")
            except Exception as e:
                print_status(f"Read {file_path}: {e}", "fail")
                all_passed = False
        else:
            print_status(f"Missing: {file_path}", "fail")
            all_passed = False

    return all_passed


def main():
    """Run all verification checks."""
    print("=" * 80)
    print("BT Composition Prototype - Setup Verification")
    print("=" * 80)

    results = {
        "Imports": check_imports(),
        "Action Nodes": check_nodes(),
        "Manual BTs": check_manual_bts(),
        "Validation": check_validation(),
        "Skill Files": check_skill_files(),
    }

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    all_passed = True
    for check_name, passed in results.items():
        status = "pass" if passed else "fail"
        print_status(check_name, status)
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)

    if all_passed:
        print(f"{GREEN}✓ All checks passed!{RESET}")
        print("\nNext steps:")
        print("  1. Ensure ROS2 Turtlesim with rosbridge is running")
        print("  2. Test manual example:")
        print(
            "     python execution/run_bt.py bt_library/manual_examples/draw_square.py"
        )
        print("  3. Upload SKILL.md to Claude for BT generation")
        return 0
    else:
        print(f"{RED}✗ Some checks failed{RESET}")
        print("\nPlease fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
