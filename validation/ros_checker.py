"""
ROS checker for behavior tree validation.

Validates that referenced ROS topics and services exist and are accessible.
Loads action definitions from action_library.yaml for domain-agnostic validation.
"""

import ast
import os
import yaml
from typing import Tuple, List, Set, Dict, Optional
import logging


class BTROSChecker:
    """
    Validates ROS dependencies in behavior tree files.

    This checker:
    - Loads action definitions from action_library.yaml
    - Extracts action node usage from BT file
    - Checks if actions are known/supported
    - Validates required ROS topics/services (if ROS connection available)
    - Provides warnings for missing dependencies
    """

    def __init__(self, check_ros_live: bool = False, action_library_path: Optional[str] = None):
        """
        Initialize the ROS checker.

        Args:
            check_ros_live: If True, attempt to check actual ROS topics/services
                           (requires rosbridge connection)
            action_library_path: Path to action_library.yaml. If None, uses default path.
        """
        self.check_ros_live = check_ros_live
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.logger = logging.getLogger("BTROSChecker")

        # Load action library
        self.known_actions = self._load_action_library(action_library_path)

    def _load_action_library(self, action_library_path: Optional[str] = None) -> Dict[str, Dict]:
        """
        Load action definitions from action_library.yaml.

        Args:
            action_library_path: Path to action library YAML file

        Returns:
            Dictionary of action names to their definitions
        """
        if action_library_path is None:
            # Default path: project_root/action_library/action_library.yaml
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            action_library_path = os.path.join(project_root, "action_library", "action_library.yaml")

        if not os.path.exists(action_library_path):
            self.logger.warning(f"Action library not found at {action_library_path}")
            return {}

        try:
            with open(action_library_path, 'r') as f:
                library = yaml.safe_load(f)

            # Parse library into known_actions format
            known_actions = {}

            # Process primitives
            if 'primitives' in library:
                for action_name, action_def in library['primitives'].items():
                    known_actions[action_name] = {
                        "package": action_def.get("package", ""),
                        "topics": action_def.get("ros_dependencies", {}).get("topics", []),
                        "services": action_def.get("ros_dependencies", {}).get("services", [])
                    }

            # Process composites
            if 'composites' in library:
                for action_name, action_def in library['composites'].items():
                    known_actions[action_name] = {
                        "package": action_def.get("package", ""),
                        "topics": action_def.get("ros_dependencies", {}).get("topics", []),
                        "services": action_def.get("ros_dependencies", {}).get("services", [])
                    }

            return known_actions

        except Exception as e:
            self.logger.error(f"Failed to load action library: {e}")
            return {}

    def check_file(self, file_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        Check a BT Python file for ROS-related issues.

        Args:
            file_path: Path to the BT Python file

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Check file exists
        if not os.path.exists(file_path):
            self.errors.append(f"File not found: {file_path}")
            return False, self.errors, self.warnings

        # Read and parse file
        try:
            with open(file_path, "r") as f:
                content = f.read()
            tree = ast.parse(content, filename=file_path)
        except Exception as e:
            self.errors.append(f"Failed to parse file: {e}")
            return False, self.errors, self.warnings

        # Extract action node usage
        used_actions = self._extract_used_actions(tree)

        # Check each action
        required_topics = set()
        required_services = set()
        unknown_actions = []

        for action_name in used_actions:
            if action_name in self.known_actions:
                action_info = self.known_actions[action_name]
                required_topics.update(action_info["topics"])
                required_services.update(action_info["services"])
            else:
                unknown_actions.append(action_name)

        # Report unknown actions
        if unknown_actions:
            self.warnings.append(
                f"Unknown action nodes used: {', '.join(unknown_actions)}. "
                "These may be custom nodes not in the action library."
            )

        # Check ROS availability (if requested)
        if self.check_ros_live:
            missing_topics, missing_services = self._check_ros_availability(
                required_topics, required_services
            )

            if missing_topics:
                self.errors.append(
                    f"Required ROS topics not available: {', '.join(missing_topics)}"
                )

            if missing_services:
                self.errors.append(
                    f"Required ROS services not available: {', '.join(missing_services)}"
                )
        else:
            # Just report what's needed
            if required_topics:
                self.warnings.append(
                    f"This BT requires ROS topics: {', '.join(required_topics)}"
                )
            if required_services:
                self.warnings.append(
                    f"This BT requires ROS services: {', '.join(required_services)}"
                )

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _extract_used_actions(self, tree: ast.AST) -> Set[str]:
        """Extract all action node class names used in the BT."""
        used_actions = set()

        for node in ast.walk(tree):
            # Look for Call nodes (function/class calls)
            if isinstance(node, ast.Call):
                # Get the function/class name
                if isinstance(node.func, ast.Name):
                    # Direct call: GoToPose(...)
                    used_actions.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    # Attribute call: module.GoToPose(...)
                    used_actions.add(node.func.attr)

        return used_actions

    def _check_ros_availability(
        self, topics: Set[str], services: Set[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Check if ROS topics and services are available.

        This is a placeholder that would integrate with ros-mcp-server
        or roslibpy to check actual ROS availability.

        Args:
            topics: Set of required topic names
            services: Set of required service names

        Returns:
            Tuple of (missing_topics, missing_services)
        """
        missing_topics = []
        missing_services = []

        try:
            from roslibpy import Ros
            import time

            # Try to connect
            ros = Ros(host="localhost", port=9090)
            ros.run()
            time.sleep(0.5)

            if not ros.is_connected:
                self.warnings.append(
                    "Could not connect to ROS to verify topics/services"
                )
                ros.terminate()
                return list(topics), list(services)

            # Get available topics (this is simplified - roslibpy doesn't have direct topic listing)
            # In a real implementation, you'd use ros-mcp-server tools here
            self.warnings.append(
                "Live ROS checking is limited. Use ros-mcp-server for comprehensive checks."
            )

            ros.terminate()

        except Exception as e:
            self.warnings.append(f"Could not check ROS availability: {e}")
            return list(topics), list(services)

        return missing_topics, missing_services


def validate_bt_ros(
    file_path: str, check_live: bool = False
) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function to validate ROS dependencies in a BT file.

    Args:
        file_path: Path to the BT Python file
        check_live: If True, check actual ROS availability

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    checker = BTROSChecker(check_ros_live=check_live)
    return checker.check_file(file_path)


def get_action_library(action_library_path: Optional[str] = None) -> Dict[str, Dict]:
    """
    Get the library of known actions and their ROS dependencies.

    Args:
        action_library_path: Path to action library YAML file. If None, uses default path.

    Returns:
        Dictionary of action names to their ROS dependencies
    """
    checker = BTROSChecker(check_ros_live=False, action_library_path=action_library_path)
    return checker.known_actions.copy()


if __name__ == "__main__":
    """
    Run ROS checker from command line.

    Usage:
        python validation/ros_checker.py path/to/bt_file.py [--check-live]
    """
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python validation/ros_checker.py path/to/bt_file.py [--check-live]"
        )
        sys.exit(1)

    file_path = sys.argv[1]
    check_live = "--check-live" in sys.argv

    print(f"Checking ROS dependencies of: {file_path}")
    if check_live:
        print("(Live ROS checking enabled)")
    print("=" * 80)

    is_valid, errors, warnings = validate_bt_ros(file_path, check_live=check_live)

    if errors:
        print("\nERRORS:")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print("\nWARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")

    if is_valid:
        print("\n✓ ROS check PASSED")
        sys.exit(0)
    else:
        print("\n✗ ROS check FAILED")
        sys.exit(1)
