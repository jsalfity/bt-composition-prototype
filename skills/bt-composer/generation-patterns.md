# BT Generation Patterns Reference

This file contains detailed patterns, examples, and structures for generating behavior trees. Only loaded when detailed pattern guidance is needed.

---

## py_trees Composite Patterns

### Sequence (Ordered Execution)

Execute children in order until one fails or all succeed.

```python
root = py_trees.composites.Sequence(name="MainTask", memory=True)
root.add_children([action1, action2, action3])
```

**Behavior:** Returns SUCCESS if all children succeed, FAILURE if any child fails.

**Use When:** Actions must execute in a specific order (e.g., setup → execute → cleanup).

---

### Selector (Fallback/OR Logic)

Execute children in order until one succeeds.

```python
fallback = py_trees.composites.Selector(name="TryAlternatives", memory=True)
fallback.add_children([primary_action, backup_action])
```

**Behavior:** Returns SUCCESS if any child succeeds, FAILURE if all children fail.

**Use When:** Want fallback options or trying alternatives.

---

### Parallel (Concurrent Execution)

Execute all children concurrently.

```python
parallel = py_trees.composites.Parallel(
    name="ConcurrentActions",
    policy=py_trees.common.ParallelPolicy.SuccessOnAll()
)
parallel.add_children([action1, action2])
```

**Behavior:** Returns based on policy (SuccessOnAll, SuccessOnOne).

**Use When:** Actions can run simultaneously.

---

## Common BT Patterns

### Pattern 1: Setup → Execute

Configure state, then perform action.

```python
root = py_trees.composites.Sequence(name="DrawTask", memory=True)
setup = SetPen(name="SetColor", r=255, g=0, b=0, width=3)
action = GoToPose(name="Move", x=5.0, y=5.0)
root.add_children([setup, action])
```

**Use Cases:**
- Setting pen color before drawing
- Configuring robot state before movement
- Loading parameters before execution

---

### Pattern 2: Conditional Execution

Check condition, then execute if valid.

```python
root = py_trees.composites.Sequence(name="SafeMove", memory=True)
check = CheckBounds(name="VerifySafe", min_x=1.0, max_x=10.0, min_y=1.0, max_y=10.0)
action = GoToPose(name="Move", x=8.0, y=8.0)
root.add_children([check, action])
```

**Use Cases:**
- Boundary checking before movement
- Precondition validation
- Safety checks

---

### Pattern 3: Move Without Drawing

Reposition without leaving a trail.

```python
sequence = py_trees.composites.Sequence(name="Reposition", memory=True)
pen_up = PenUp(name="LiftPen")
move = GoToPose(name="Move", x=3.0, y=3.0)
pen_down = PenDown(name="LowerPen", r=0, g=0, b=255, width=3)
sequence.add_children([pen_up, move, pen_down])
```

**Use Cases:**
- Repositioning between shapes
- Moving to start position
- Creating gaps in drawings

---

### Pattern 4: Multi-Step Drawing

Draw complex shapes with multiple segments.

```python
root = py_trees.composites.Sequence(name="DrawShape", memory=True)
set_color = SetPen(name="SetRed", r=255, g=0, b=0, width=3)
point1 = GoToPose(name="Point1", x=3.0, y=3.0)
point2 = GoToPose(name="Point2", x=5.0, y=3.0)
point3 = GoToPose(name="Point3", x=5.0, y=5.0)
point4 = GoToPose(name="Point4", x=3.0, y=5.0)
point5 = GoToPose(name="Point5", x=3.0, y=3.0)  # Close shape
root.add_children([set_color, point1, point2, point3, point4, point5])
```

**Use Cases:**
- Drawing polygons
- Creating custom paths
- Connecting multiple points

---

### Pattern 5: Using Composite Actions

Leverage high-level actions for common shapes.

```python
root = py_trees.composites.Sequence(name="DrawCircle", memory=True)
circle = DrawShape(
    name="RedCircle",
    shape_type="circle",
    size=2.0,
    center_x=5.5,
    center_y=5.5,
    color=(255, 0, 0),
    width=3
)
root.add_children([circle])
```

**Available Shapes:**
- `circle` - Draws circular path
- `square` - Draws square
- `triangle` - Draws triangle

---

## Validation Tiers (For Generation Loop)

### Tier 1: Critical (Must Pass)

Errors that **prevent execution**:

- Valid Python syntax (AST parsing)
- `create_root()` function exists
- Returns `py_trees.behaviour.Behaviour` object
- All imports available
- All action nodes exist in action library

**Action:** MUST regenerate if Tier 1 fails

---

### Tier 2: Important (Should Pass)

Errors that indicate **logical problems**:

- Parameters within valid ranges
- Required parameters provided
- Parameter types correct
- RGB values in [0, 255]
- Coordinates in valid workspace

**Action:** Should fix but not blocking

---

### Tier 3: Advisory (Nice to Have)

Warnings that suggest **improvements**:

- Reasonable action ordering
- No obvious infinite loops
- No unreachable code paths

**Action:** Informational only

---

## Common Generation Errors

### Error: Wrong Function Name

```python
# ❌ Wrong
def create_behavior_tree():
    return root

# ✅ Correct
def create_root():
    return root
```

---

### Error: Invalid Parameters

```python
# ❌ Wrong - outside bounds
GoToPose(x=15, y=15)

# ✅ Correct - within [0,11]
GoToPose(x=8.0, y=8.0)
```

---

### Error: Missing Imports

```python
# ❌ Wrong - using action without importing
def create_root():
    root = py_trees.composites.Sequence(name="Task", memory=True)
    root.add_children([GoToPose(name="Move", x=5.0, y=5.0)])
    return root

# ✅ Correct - import before using
from py_trees_nodes.primitives import GoToPose

def create_root():
    root = py_trees.composites.Sequence(name="Task", memory=True)
    root.add_children([GoToPose(name="Move", x=5.0, y=5.0)])
    return root
```

---

### Error: Wrong File Location

```python
# ❌ Wrong
/mnt/user-data/outputs/my_bt.py

# ✅ Correct
generated_bts/my_bt.py
```

---

## Working Examples to Reference

Study these actual working examples:

**In `bt_library/manual_examples/`:**
- `draw_square.py` - Simple sequence with SetPen + GoToPose
- `patrol_waypoints.py` - Using PatrolWaypoints composite

**In `generated_bts/`:**
- `draw_star.py` - Using PenUp/PenDown with calculated positions
- `draw_x_pattern.py` - Multiple shape drawing
- `circle_and_conditional_line.py` - Conditional color changes

---

## Iterative Refinement Process

When validation fails:

1. **Read validation JSON output carefully**
2. **Check tier level:**
   - Tier 1 = MUST fix (regenerate)
   - Tier 2 = Should fix
   - Tier 3 = Advisory
3. **Identify specific error:**
   - Syntax error?
   - Wrong function name?
   - Parameter out of bounds?
   - Missing import?
4. **Regenerate with specific fixes**
5. **Re-validate**
6. **Repeat up to 3 times total**

If still failing after 3 attempts:
- Explain limitation to user
- Show what errors remain
- Suggest simplifying the task

---

## Best Practices

1. **Always use `memory=True` for Sequences** - This is the standard pattern
2. **Stay within safe bounds** - Use x,y in [1.0, 10.0] to avoid edge wrapping
3. **Follow the template exactly** - Especially imports and `create_root()` name
4. **Use action_library.yaml as ground truth** - Don't invent actions
5. **Always validate before returning** - This is mandatory
6. **Lift pen when not drawing** - Use PenUp() to reposition without drawing
7. **Close shapes** - Return to starting point to complete shapes
