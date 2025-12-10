"""
Syntax checker for generated behavior trees.

Uses Python AST to validate syntax and basic structure of generated BT files.
"""

import ast
import os
from typing import Tuple, List


class BTSyntaxChecker:
    """
    Validates the syntax and structure of behavior tree Python files.

    This checker performs:
    - Python syntax validation using AST
    - Checks for required imports
    - Checks for create_root() function definition
    - Basic structure validation
    """

    REQUIRED_IMPORTS = ["py_trees"]
    REQUIRED_FUNCTION = "create_root"

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def check_file(self, file_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        Check a BT Python file for syntax and structure issues.

        Args:
            file_path: Path to the BT Python file

        Returns:
            Tuple of (is_valid, errors, warnings)
            - is_valid: True if file passes all checks
            - errors: List of error messages
            - warnings: List of warning messages
        """
        self.errors = []
        self.warnings = []

        # Check file exists
        if not os.path.exists(file_path):
            self.errors.append(f"File not found: {file_path}")
            return False, self.errors, self.warnings

        # Read file content
        try:
            with open(file_path, "r") as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Failed to read file: {e}")
            return False, self.errors, self.warnings

        # Check syntax by parsing AST
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            self.errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return False, self.errors, self.warnings
        except Exception as e:
            self.errors.append(f"Failed to parse file: {e}")
            return False, self.errors, self.warnings

        # Analyze AST
        self._check_imports(tree)
        self._check_create_root_function(tree)

        # Determine if valid (no errors, warnings are OK)
        is_valid = len(self.errors) == 0

        return is_valid, self.errors, self.warnings

    def _check_imports(self, tree: ast.AST):
        """Check for required imports."""
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])

        # Check for py_trees import
        if "py_trees" not in imports:
            self.errors.append("Missing required import: py_trees")

        # Check for common imports (warnings only)
        if "sys" not in imports:
            self.warnings.append(
                "Missing 'sys' import - may be needed for path manipulation"
            )

    def _check_create_root_function(self, tree: ast.AST):
        """Check for create_root() function definition."""
        has_create_root = False
        create_root_returns = False

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name == self.REQUIRED_FUNCTION:
                    has_create_root = True

                    # Check if function has a return statement
                    for child in ast.walk(node):
                        if isinstance(child, ast.Return) and child.value is not None:
                            create_root_returns = True
                            break

        if not has_create_root:
            self.errors.append(f"Missing required function: {self.REQUIRED_FUNCTION}()")
        elif not create_root_returns:
            self.errors.append(
                f"Function {self.REQUIRED_FUNCTION}() must return a behavior tree root node"
            )


def validate_bt_syntax(file_path: str) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function to validate a BT file.

    Args:
        file_path: Path to the BT Python file

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    checker = BTSyntaxChecker()
    return checker.check_file(file_path)


if __name__ == "__main__":
    """
    Run syntax checker from command line.

    Usage:
        python validation/syntax_checker.py path/to/bt_file.py
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python validation/syntax_checker.py path/to/bt_file.py")
        sys.exit(1)

    file_path = sys.argv[1]

    print(f"Checking syntax of: {file_path}")
    print("=" * 80)

    is_valid, errors, warnings = validate_bt_syntax(file_path)

    if errors:
        print("\nERRORS:")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print("\nWARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")

    if is_valid:
        print("\n✓ Syntax check PASSED")
        sys.exit(0)
    else:
        print("\n✗ Syntax check FAILED")
        sys.exit(1)
