"""
Validation orchestrator for behavior trees.

Runs multi-tier validation on generated BT files:
- Tier 1: Critical (syntax, imports, action existence)
- Tier 2: Important (parameter constraints, types)
- Tier 3: Advisory (semantic checks, best practices)

Usage:
    python validation/orchestrator.py path/to/bt_file.py [--verbose]
"""

import sys
import os
import json
import ast
import yaml
from typing import Dict, List, Tuple, Any

# Import existing validators
from validation.syntax_checker import BTSyntaxChecker
from validation.ros_checker import BTROSChecker, KNOWN_ACTIONS


class BTValidationOrchestrator:
    """
    Orchestrates multi-tier validation of behavior tree files.
    """

    def __init__(self, action_library_path: str = None):
        """
        Initialize the orchestrator.

        Args:
            action_library_path: Path to action_library.yaml (optional)
        """
        self.syntax_checker = BTSyntaxChecker()
        self.ros_checker = BTROSChecker(check_ros_live=False)

        # Load action library if provided
        self.action_library = {}
        if action_library_path and os.path.exists(action_library_path):
            with open(action_library_path, 'r') as f:
                self.action_library = yaml.safe_load(f)

    def validate(self, file_path: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Run complete validation on a BT file.

        Args:
            file_path: Path to the BT Python file
            verbose: If True, print detailed progress

        Returns:
            Dictionary with validation results in tier structure
        """
        if verbose:
            print(f"Validating: {file_path}")
            print("=" * 80)

        results = {
            "file": file_path,
            "valid": False,
            "tier1_critical": {
                "passed": False,
                "errors": []
            },
            "tier2_important": {
                "passed": False,
                "warnings": []
            },
            "tier3_advisory": {
                "passed": True,
                "suggestions": []
            },
            "summary": ""
        }

        # Tier 1: Critical validation
        if verbose:
            print("\n[TIER 1] Running critical validation...")

        tier1_passed, tier1_errors = self._validate_tier1(file_path, verbose)
        results["tier1_critical"]["passed"] = tier1_passed
        results["tier1_critical"]["errors"] = tier1_errors

        if not tier1_passed:
            results["summary"] = f"Validation failed with {len(tier1_errors)} critical error(s)"
            return results

        # Tier 2: Important validation (constraint checking)
        if verbose:
            print("\n[TIER 2] Running constraint validation...")

        tier2_passed, tier2_warnings = self._validate_tier2(file_path, verbose)
        results["tier2_important"]["passed"] = tier2_passed
        results["tier2_important"]["warnings"] = tier2_warnings

        # Tier 3: Advisory (semantic checks)
        if verbose:
            print("\n[TIER 3] Running advisory checks...")

        tier3_suggestions = self._validate_tier3(file_path, verbose)
        results["tier3_advisory"]["suggestions"] = tier3_suggestions

        # Overall validation result
        results["valid"] = tier1_passed and tier2_passed

        # Generate summary
        if results["valid"]:
            if tier3_suggestions:
                results["summary"] = f"All validation checks passed ({len(tier3_suggestions)} suggestion(s))"
            else:
                results["summary"] = "All validation checks passed"
        else:
            error_count = len(tier1_errors)
            warning_count = len(tier2_warnings)
            results["summary"] = f"Validation failed with {error_count} critical error(s) and {warning_count} warning(s)"

        return results

    def _validate_tier1(self, file_path: str, verbose: bool) -> Tuple[bool, List[str]]:
        """
        Tier 1: Critical validation (syntax and action existence).

        Returns:
            Tuple of (passed, errors)
        """
        all_errors = []

        # 1. Syntax validation
        is_valid, errors, warnings = self.syntax_checker.check_file(file_path)
        if not is_valid:
            all_errors.extend(errors)
            if verbose:
                print(f"  ✗ Syntax check failed: {len(errors)} error(s)")
        else:
            if verbose:
                print("  ✓ Syntax check passed")

        # 2. ROS/Action existence validation
        is_valid, errors, warnings = self.ros_checker.check_file(file_path)
        if not is_valid:
            all_errors.extend(errors)
            if verbose:
                print(f"  ✗ Action check failed: {len(errors)} error(s)")
        else:
            if verbose:
                print("  ✓ Action check passed")

        return len(all_errors) == 0, all_errors

    def _validate_tier2(self, file_path: str, verbose: bool) -> Tuple[bool, List[str]]:
        """
        Tier 2: Important validation (parameter constraints).

        Returns:
            Tuple of (passed, warnings)
        """
        warnings = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            tree = ast.parse(content)

            # Check parameter constraints
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        action_name = node.func.id

                        # Check known actions
                        if action_name in KNOWN_ACTIONS:
                            # Validate parameters
                            for keyword in node.keywords:
                                param_name = keyword.arg

                                try:
                                    param_value = ast.literal_eval(keyword.value)
                                except:
                                    continue

                                # Check spatial constraints
                                if action_name == "GoToPose":
                                    if param_name == "x" and not (0 <= param_value <= 11):
                                        warnings.append(
                                            f"Parameter 'x' value {param_value} outside valid range [0, 11]"
                                        )
                                    elif param_name == "y" and not (0 <= param_value <= 11):
                                        warnings.append(
                                            f"Parameter 'y' value {param_value} outside valid range [0, 11]"
                                        )

                                # Check color constraints
                                if action_name in ["SetPen", "PenDown"]:
                                    if param_name in ["r", "g", "b"]:
                                        if not (0 <= param_value <= 255):
                                            warnings.append(
                                                f"Parameter '{param_name}' value {param_value} outside valid range [0, 255]"
                                            )

            if verbose:
                if warnings:
                    print(f"  ⚠ Found {len(warnings)} constraint warning(s)")
                else:
                    print("  ✓ All constraints satisfied")

        except Exception as e:
            warnings.append(f"Failed to check constraints: {e}")
            if verbose:
                print(f"  ✗ Constraint check error: {e}")

        return len(warnings) == 0, warnings

    def _validate_tier3(self, file_path: str, verbose: bool) -> List[str]:
        """
        Tier 3: Advisory validation (semantic checks).

        Returns:
            List of suggestions
        """
        suggestions = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            tree = ast.parse(content)

            # Check for common patterns
            # 1. Check if SetPen is used before drawing
            # 2. Check for reasonable bounds usage
            # 3. Check for duplicate node names (basic)

            # Simple check: count actions
            action_count = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in KNOWN_ACTIONS:
                            action_count += 1

            if action_count == 0:
                suggestions.append("Behavior tree appears to have no actions")

            if action_count > 50:
                suggestions.append(
                    f"Behavior tree has {action_count} actions - consider using composite actions"
                )

            if verbose:
                if suggestions:
                    print(f"  💡 Found {len(suggestions)} suggestion(s)")
                else:
                    print("  ✓ No advisory suggestions")

        except Exception as e:
            if verbose:
                print(f"  ⚠ Advisory check skipped: {e}")

        return suggestions


def main():
    """
    Main entry point for command-line usage.
    """
    if len(sys.argv) < 2:
        print("Usage: python validation/orchestrator.py path/to/bt_file.py [--verbose]")
        sys.exit(1)

    file_path = sys.argv[1]
    verbose = "--verbose" in sys.argv

    # Find action library
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    action_library_path = os.path.join(
        project_root,
        "skills/bt-composer/action_library.yaml"
    )

    # Run validation
    orchestrator = BTValidationOrchestrator(action_library_path=action_library_path)
    results = orchestrator.validate(file_path, verbose=verbose)

    # Output results as JSON
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print(json.dumps(results, indent=2))

    # Exit with appropriate code
    if results["valid"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
