"""
Structural checker for behavior trees.

Performs domain-agnostic structural and reachability validation on BT files.
These checks focus on BT structure and py_trees best practices, without
any domain-specific knowledge (e.g., turtlesim, robotics, etc.).
"""

import ast
import os
from typing import Tuple, List


class BTStructuralChecker:
    """
    Validates the structural integrity and reachability of behavior trees.

    This checker performs:
    - Duplicate node name detection
    - Missing memory parameter checks for composites
    - Empty composite detection (future)
    - Unreachable branch detection (future)
    """

    def __init__(self):
        self.suggestions: List[str] = []

    def check_file(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Check a BT Python file for structural issues.

        Args:
            file_path: Path to the BT Python file

        Returns:
            Tuple of (is_valid, suggestions)
            - is_valid: Always True (these are suggestions, not errors)
            - suggestions: List of advisory messages
        """
        self.suggestions = []

        # Check file exists
        if not os.path.exists(file_path):
            self.suggestions.append(f"File not found: {file_path}")
            return True, self.suggestions

        # Read and parse file
        try:
            with open(file_path, "r") as f:
                content = f.read()
            tree = ast.parse(content, filename=file_path)
        except Exception as e:
            self.suggestions.append(f"Failed to parse file: {e}")
            return True, self.suggestions

        # Run structural checks
        self._check_duplicate_names(tree)
        self._check_missing_memory_parameter(tree)

        # Always valid - these are suggestions only
        return True, self.suggestions

    def _check_duplicate_names(self, tree: ast.AST):
        """Check for duplicate node names in the behavior tree."""
        node_names = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "name":
                        try:
                            name_value = ast.literal_eval(keyword.value)
                            if isinstance(name_value, str):
                                node_names.append(name_value)
                        except:
                            pass

        # Find duplicates
        seen = set()
        duplicates = set()
        for name in node_names:
            if name in seen:
                duplicates.add(name)
            seen.add(name)

        if duplicates:
            dup_list = sorted(list(duplicates))[:5]  # Limit to first 5
            self.suggestions.append(
                f"Duplicate node names found: {', '.join(dup_list)} - may complicate debugging"
            )

    def _check_missing_memory_parameter(self, tree: ast.AST):
        """Check if Sequence/Selector nodes are missing memory=True parameter."""
        composite_types = ["Sequence", "Selector"]
        missing_memory_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if this is a Sequence or Selector
                is_composite = False
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in composite_types:
                        is_composite = True
                elif isinstance(node.func, ast.Name):
                    if node.func.id in composite_types:
                        is_composite = True

                if is_composite:
                    # Check if memory parameter is present
                    has_memory = False
                    for keyword in node.keywords:
                        if keyword.arg == "memory":
                            has_memory = True
                            break

                    if not has_memory:
                        missing_memory_count += 1

        if missing_memory_count > 0:
            self.suggestions.append(
                f"Found {missing_memory_count} Sequence/Selector node(s) without 'memory=True' parameter - recommended for proper state management"
            )


def validate_bt_structure(file_path: str) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate BT structure.

    Args:
        file_path: Path to the BT Python file

    Returns:
        Tuple of (is_valid, suggestions)
    """
    checker = BTStructuralChecker()
    return checker.check_file(file_path)


if __name__ == "__main__":
    """
    Run structural checker from command line.

    Usage:
        python validation/structural_checker.py path/to/bt_file.py
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python validation/structural_checker.py path/to/bt_file.py")
        sys.exit(1)

    file_path = sys.argv[1]

    print(f"Checking structure of: {file_path}")
    print("=" * 80)

    is_valid, suggestions = validate_bt_structure(file_path)

    if suggestions:
        print("\nSUGGESTIONS:")
        for suggestion in suggestions:
            print(f"  💡 {suggestion}")
    else:
        print("\n✓ No structural issues found")

    print("\n✓ Structural check completed")
    sys.exit(0)
