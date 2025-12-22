"""
Validation orchestrator for behavior trees.

Runs multi-tier validation on generated BT files:
- Tier 1: Critical (syntax, imports, action existence)
- Tier 2: Structural (reachability, duplicate names, memory parameters)
- Tier 3: Semantic (LLM-based validation - reserved for future use)

All validation is domain-agnostic and environment-independent.

Usage:
    python validation/orchestrator.py path/to/bt_file.py [--verbose]
"""

import sys
import json
from typing import Dict, List, Tuple, Any

# Import existing validators
from validation.syntax_checker import BTSyntaxChecker
from validation.ros_checker import BTROSChecker
from validation.structural_checker import BTStructuralChecker


class BTValidationOrchestrator:
    """
    Orchestrates multi-tier validation of behavior tree files.
    """

    def __init__(self):
        """
        Initialize the orchestrator.
        """
        self.syntax_checker = BTSyntaxChecker()
        self.ros_checker = BTROSChecker(check_ros_live=False)
        self.structural_checker = BTStructuralChecker()

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
            "tier2_structural": {
                "passed": True,
                "suggestions": []
            },
            "tier3_semantic": {
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

        # Tier 2: Structural validation
        if verbose:
            print("\n[TIER 2] Running structural validation...")

        tier2_suggestions = self._validate_tier2(file_path, verbose)
        results["tier2_structural"]["suggestions"] = tier2_suggestions

        # Tier 3: Semantic validation (LLM-based, reserved for future)
        if verbose:
            print("\n[TIER 3] Running semantic validation...")

        tier3_suggestions = self._validate_tier3(file_path, verbose)
        results["tier3_semantic"]["suggestions"] = tier3_suggestions

        # Overall validation result (only Tier 1 affects validity)
        results["valid"] = tier1_passed

        # Generate summary
        total_suggestions = len(tier2_suggestions) + len(tier3_suggestions)
        if results["valid"]:
            if total_suggestions > 0:
                results["summary"] = f"All validation checks passed ({total_suggestions} suggestion(s))"
            else:
                results["summary"] = "All validation checks passed"
        else:
            results["summary"] = f"Validation failed with {len(tier1_errors)} critical error(s)"

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

    def _validate_tier2(self, file_path: str, verbose: bool) -> List[str]:
        """
        Tier 2: Structural validation (reachability and structural checks).

        Returns:
            List of suggestions
        """
        # Run structural validation
        _, suggestions = self.structural_checker.check_file(file_path)

        if verbose:
            if suggestions:
                print(f"  💡 Found {len(suggestions)} suggestion(s)")
            else:
                print("  ✓ No structural issues found")

        return suggestions

    def _validate_tier3(self, file_path: str, verbose: bool) -> List[str]:
        """
        Tier 3: Semantic validation (LLM-based, reserved for future use).

        This tier is reserved for future LLM-based semantic validation, such as:
        - Action ordering (e.g., sense before pick)
        - Precondition checking
        - Goal achievability
        - State transition validation

        Returns:
            List of suggestions
        """
        suggestions = []

        if verbose:
            print("  ✓ No Tier 3 checks configured")

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

    # Run validation
    orchestrator = BTValidationOrchestrator()
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
