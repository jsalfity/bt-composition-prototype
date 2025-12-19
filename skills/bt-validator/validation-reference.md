# BT Validation Reference

This file contains detailed validation tier descriptions, error catalogs, and troubleshooting guidance. Only loaded when detailed validation information is needed.

---

## Validation Tiers

### Tier 1: Critical (Must Pass)

Errors at this tier **prevent execution** and will cause runtime failures.

**Checks:**
- Valid Python syntax (AST parsing)
- `create_root()` function exists
- `create_root()` returns `py_trees.behaviour.Behaviour` object
- All imports are available
- All action nodes exist in action library
- Correct py_trees API usage

**Tools:**
- `validation/syntax_checker.py` - Syntax and structure validation
- `validation/ros_checker.py` - Action existence verification

**Action:** MUST regenerate if Tier 1 fails

---

### Tier 2: Important (Should Pass)

Errors at this tier indicate **logical problems** that may cause unexpected behavior.

**Checks:**
- Parameters within valid ranges (e.g., x,y in workspace bounds)
- Required parameters provided
- Parameter types correct (int, float, str, etc.)
- Color values in valid range (RGB in [0, 255])
- Reasonable parameter values

**Tools:**
- `validation/orchestrator.py` - Constraint and type checking

**Action:** Should fix but not blocking if reasonable

---

### Tier 3: Advisory (Nice to Have)

Warnings that suggest **improvements** but don't block execution.

**Checks:**
- Reasonable action ordering
- No obvious infinite loops
- No unreachable code paths
- Best practice adherence

**Tools:**
- Manual review or future LLM-as-judge

**Action:** Informational only

---

## Complete Error Catalog

### Tier 1 Errors (Critical)

#### Error: Missing create_root() function

**Symptom:**
```
Missing required function: create_root()
```

**Cause:** Function has wrong name or doesn't exist

**Fix:**
```python
# ❌ Wrong
def create_behavior_tree():
    return root

def generate_tree():
    return root

# ✅ Correct
def create_root():
    return root
```

---

#### Error: Wrong return type

**Symptom:**
```
create_root() must return py_trees.behaviour.Behaviour object
```

**Cause:** Function returns None, wrong type, or nothing

**Fix:**
```python
# ❌ Wrong
def create_root():
    root = py_trees.composites.Sequence(name="Task", memory=True)
    # Missing return

# ❌ Wrong
def create_root():
    return None

# ✅ Correct
def create_root() -> py_trees.behaviour.Behaviour:
    root = py_trees.composites.Sequence(name="Task", memory=True)
    root.add_children([...])
    return root
```

---

#### Error: Invalid imports

**Symptom:**
```
Invalid import: UnknownAction not found
ImportError: cannot import name 'CustomAction'
```

**Cause:** Importing action that doesn't exist in action library

**Fix:**
```python
# ❌ Wrong
from py_trees_nodes import GoToPose
from py_trees_nodes.primitives import CustomAction

# ✅ Correct
from py_trees_nodes.primitives import GoToPose, SetPen, PenUp, PenDown
from py_trees_nodes.composites import DrawShape, PatrolWaypoints
```

---

#### Error: Syntax errors

**Symptom:**
```
SyntaxError: invalid syntax at line X
```

**Cause:** Invalid Python code

**Fix:**
- Check for missing colons, parentheses, brackets
- Check for incorrect indentation
- Validate string quotes are closed
- Ensure proper function/class definitions

---

#### Error: Unknown action node

**Symptom:**
```
Action 'CustomMove' not found in action library
```

**Cause:** Using action that isn't in the discovered action catalog

**Fix:**
```python
# ❌ Wrong - action doesn't exist
CustomMove(name="Move", x=5.0, y=5.0)

# ✅ Correct - use action from library
GoToPose(name="Move", x=5.0, y=5.0)
```

---

### Tier 2 Warnings (Important)

#### Warning: Parameters out of bounds

**Symptom:**
```
Parameter 'x' value 15.0 outside valid range [0, 11]
Parameter 'y' value -2.0 outside valid range [0, 11]
```

**Cause:** Coordinate outside workspace bounds

**Fix:**
```python
# ⚠️ Warning
GoToPose(name="Move", x=15.0, y=15.0)  # Outside [0,11]
GoToPose(name="Move", x=-1.0, y=5.0)   # Negative coordinate

# ✅ Fixed
GoToPose(name="Move", x=8.0, y=8.0)    # Within bounds
GoToPose(name="Move", x=2.0, y=5.0)    # Positive coordinates
```

---

#### Warning: Invalid color values

**Symptom:**
```
Parameter 'r' value 300 outside valid range [0, 255]
Parameter 'g' value -10 outside valid range [0, 255]
```

**Cause:** RGB values outside valid range

**Fix:**
```python
# ⚠️ Warning
SetPen(name="Red", r=300, g=0, b=0)     # RGB > 255
SetPen(name="Blue", r=0, g=-10, b=255)  # Negative RGB

# ✅ Fixed
SetPen(name="Red", r=255, g=0, b=0)     # RGB in [0,255]
SetPen(name="Blue", r=0, g=0, b=255)    # Valid RGB
```

---

#### Warning: Missing required parameters

**Symptom:**
```
Missing required parameter 'x' for action GoToPose
Missing required parameter 'name' for action SetPen
```

**Cause:** Required parameter not provided

**Fix:**
```python
# ⚠️ Warning
GoToPose(y=5.0)                        # Missing x
SetPen(r=255, g=0, b=0)                # Missing name

# ✅ Fixed
GoToPose(name="Move", x=5.0, y=5.0)    # All required params
SetPen(name="Red", r=255, g=0, b=0)    # All required params
```

---

#### Warning: Wrong parameter types

**Symptom:**
```
Parameter 'x' expects float, got str
Parameter 'r' expects int, got float
```

**Cause:** Parameter has wrong type

**Fix:**
```python
# ⚠️ Warning
GoToPose(name="Move", x="5.0", y="5.0")  # Strings instead of floats
SetPen(name="Red", r=255.5, g=0, b=0)    # Float instead of int

# ✅ Fixed
GoToPose(name="Move", x=5.0, y=5.0)      # Floats
SetPen(name="Red", r=255, g=0, b=0)      # Ints
```

---

### Tier 3 Suggestions (Advisory)

#### Suggestion: Illogical action ordering

**Symptom:**
```
Suggestion: PenDown without pen color configuration
Suggestion: Movement before pen setup
```

**Cause:** Actions in unexpected order

**Improvement:**
```python
# 💡 Could be improved
sequence = py_trees.composites.Sequence(name="Draw", memory=True)
sequence.add_children([
    GoToPose(name="Move", x=5.0, y=5.0),  # Moving first
    SetPen(name="Red", r=255, g=0, b=0)   # Then setting color
])

# ✅ Better
sequence = py_trees.composites.Sequence(name="Draw", memory=True)
sequence.add_children([
    SetPen(name="Red", r=255, g=0, b=0),  # Set color first
    GoToPose(name="Move", x=5.0, y=5.0)   # Then move
])
```

---

#### Suggestion: Potential infinite loops

**Symptom:**
```
Suggestion: Selector with no terminal condition may loop infinitely
```

**Improvement:**
Use timeout or explicit terminal conditions.

---

#### Suggestion: Unreachable code

**Symptom:**
```
Suggestion: Actions after this point may never execute
```

**Improvement:**
Restructure tree to ensure all branches are reachable.

---

## Validation Output Format

### Success Response

```json
{
  "file": "generated_bts/example.py",
  "valid": true,
  "tier1_critical": {
    "passed": true,
    "errors": []
  },
  "tier2_important": {
    "passed": true,
    "warnings": []
  },
  "tier3_advisory": {
    "passed": true,
    "suggestions": []
  },
  "summary": "All validation checks passed"
}
```

---

### Failure Response

```json
{
  "file": "generated_bts/bad_example.py",
  "valid": false,
  "tier1_critical": {
    "passed": false,
    "errors": [
      "Missing required function: create_root()",
      "Invalid import: UnknownAction not found"
    ]
  },
  "tier2_important": {
    "passed": false,
    "warnings": [
      "Parameter 'x' value 15.0 outside valid range [0, 11]",
      "Missing required parameter 'y' for action GoToPose"
    ]
  },
  "tier3_advisory": {
    "passed": true,
    "suggestions": []
  },
  "summary": "Validation failed with 2 critical errors and 2 warnings"
}
```

---

## Troubleshooting Guide

### Problem: BT fails to execute

**Diagnostic Steps:**
1. Run full validation: `python validation/orchestrator.py {file}`
2. Check Tier 1 errors first (critical)
3. Verify `create_root()` function exists and returns Behaviour
4. Check all imports are valid
5. Ensure all actions exist in action library

---

### Problem: BT executes but behaves unexpectedly

**Diagnostic Steps:**
1. Check Tier 2 warnings (parameter bounds)
2. Verify all parameters are within valid ranges
3. Check parameter types match expectations
4. Review action ordering in tree structure

---

### Problem: Validation passes but robot doesn't move correctly

**Diagnostic Steps:**
1. Check Tier 3 suggestions (semantic issues)
2. Review action ordering
3. Verify pen up/down states
4. Check coordinate calculations
5. Ensure shapes are closed (return to start)

---

## Individual Validator Usage

### Syntax Checker Only

```bash
python validation/syntax_checker.py generated_bts/{filename}.py
```

Checks:
- Valid Python syntax
- `create_root()` exists
- Correct return type
- Import validity

---

### ROS Checker Only

```bash
python validation/ros_checker.py generated_bts/{filename}.py
```

Checks:
- All actions exist in action library
- Valid package imports

With live ROS connection:
```bash
python validation/ros_checker.py generated_bts/{filename}.py --check-live
```

---

### Full Orchestrator

```bash
python validation/orchestrator.py generated_bts/{filename}.py
```

Runs all tiers and returns comprehensive JSON report.

---

## Best Practices for Validation

1. **Always run full orchestrator** - Don't rely on individual validators alone
2. **Fix Tier 1 errors first** - These prevent execution
3. **Address Tier 2 warnings** - These cause unexpected behavior
4. **Consider Tier 3 suggestions** - These improve quality
5. **Re-validate after fixes** - Ensure changes didn't introduce new issues
6. **Max 3 regeneration attempts** - If still failing, simplify the task
