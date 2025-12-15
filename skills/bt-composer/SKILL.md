# BT Composer Skill

**Purpose**: Generate py_trees behavior trees for ROS2 Turtlesim control from natural language descriptions.

**Output**: Python files that define behavior trees using the available action library.

---

## Quick Reference

### File Structure Template

```python
"""
[Description of what this BT does]
"""

import py_trees
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from py_trees_nodes.primitives import GoToPose, SetPen, MoveDistance, GetPose, CheckBounds, PenUp, PenDown
from py_trees_nodes.composites import DrawShape, PatrolWaypoints


def create_root() -> py_trees.behaviour.Behaviour:
    """
    Create the behavior tree root node.

    Returns:
        The root node of the behavior tree
    """

    # Build your tree here
    root = py_trees.composites.Sequence(name="MainTask", memory=True)

    # Add children...

    return root


if __name__ == '__main__':
    """Direct execution for testing."""
    print("Creating behavior tree...")
    root = create_root()
    print("Tree structure:")
    print(py_trees.display.unicode_tree(root, show_status=True))
```

---

## Available Action Nodes

### Primitive Actions

#### GoToPose
**Purpose**: Navigate turtle to specific position/orientation

```python
GoToPose(
    name="MoveTo_A",
    x=5.0,           # Target x (0-11)
    y=5.0,           # Target y (0-11)
    theta=0.0,       # Target angle in radians (None to ignore)
    tolerance_pos=0.1,    # Position tolerance
    tolerance_angle=0.1   # Angular tolerance
)
```

**Returns**: SUCCESS when reached, RUNNING while moving, FAILURE on error

#### SetPen
**Purpose**: Configure pen color, width, and on/off state

```python
SetPen(
    name="SetRed",
    r=255, g=0, b=0,  # RGB values 0-255
    width=3,           # Pen width
    off=0              # 0=drawing, 1=no drawing
)
```

**Convenience shortcuts**:
- `PenUp(name="LiftPen")` - Disable drawing
- `PenDown(name="LowerPen", r=255, g=0, b=0, width=3)` - Enable drawing with color

#### MoveDistance
**Purpose**: Move forward/backward by distance

```python
MoveDistance(
    name="Forward",
    distance=2.0,  # Positive=forward, negative=backward
    speed=1.0      # Speed in m/s
)
```

#### GetPose
**Purpose**: Read current turtle position (sensing)

```python
GetPose(
    name="ReadPosition",
    blackboard_key='current_pose'  # Where to store result
)
```

Stores dict: `{'x': float, 'y': float, 'theta': float, 'linear_velocity': float, 'angular_velocity': float}`

#### CheckBounds
**Purpose**: Verify turtle is within safe area (condition)

```python
CheckBounds(
    name="SafetyCheck",
    min_x=1.0, max_x=10.0,
    min_y=1.0, max_y=10.0
)
```

**Returns**: SUCCESS if in bounds, FAILURE if out of bounds

### Compositional Actions

#### DrawShape
**Purpose**: Draw geometric shapes (circle, square, triangle)

```python
DrawShape(
    name="DrawCircle",
    shape_type='circle',  # 'circle', 'square', or 'triangle'
    size=2.0,             # Radius or side length
    center_x=5.5,         # Center position
    center_y=5.5,
    color=(0, 255, 0),    # RGB tuple
    width=3,              # Pen width
    segments=36           # Circle smoothness (more = smoother)
)
```

#### PatrolWaypoints
**Purpose**: Navigate through multiple waypoints

```python
PatrolWaypoints(
    name="Patrol",
    waypoints=[
        (3.0, 3.0),      # (x, y)
        (8.0, 3.0),
        (8.0, 8.0, 0.0), # (x, y, theta) also supported
        (3.0, 8.0)
    ],
    loop=True  # Return to start when done
)
```

---

## py_trees Composition Patterns

### Sequence (AND logic)
**Use**: Execute actions in order; all must succeed

```python
sequence = py_trees.composites.Sequence(name="DoABC", memory=True)
sequence.add_children([action_a, action_b, action_c])
```

**Behavior**:
- Executes children left-to-right
- Returns SUCCESS if all succeed
- Returns FAILURE if any fails (stops at first failure)

### Selector (OR logic)
**Use**: Try alternatives until one succeeds

```python
selector = py_trees.composites.Selector(name="TryOptions", memory=True)
selector.add_children([option_a, option_b, option_c])
```

**Behavior**:
- Executes children left-to-right
- Returns SUCCESS if any succeeds (stops at first success)
- Returns FAILURE if all fail

### Parallel (Concurrent)
**Use**: Execute multiple actions simultaneously

```python
parallel = py_trees.composites.Parallel(
    name="DoSimultaneous",
    policy=py_trees.common.ParallelPolicy.SuccessOnAll()
)
parallel.add_children([action_a, action_b])
```

**Policies**:
- `SuccessOnAll()`: All must succeed
- `SuccessOnOne()`: Any one success is enough

---

## Common Patterns

### Pattern 1: Setup � Execute
```python
root = py_trees.composites.Sequence(name="Task", memory=True)
setup = SetPen(name="SetColor", r=255, g=0, b=0, width=3, off=0)
action = GoToPose(name="Move", x=5.0, y=5.0)
root.add_children([setup, action])
```

### Pattern 2: Check Condition � Act
```python
root = py_trees.composites.Sequence(name="SafeMove", memory=True)
check = CheckBounds(name="VerifySafe", min_x=1.0, max_x=10.0, min_y=1.0, max_y=10.0)
move = GoToPose(name="Move", x=8.0, y=8.0)
root.add_children([check, move])
```

### Pattern 3: Try Multiple Approaches
```python
root = py_trees.composites.Selector(name="TryPaths", memory=True)
path_a = GoToPose(name="DirectPath", x=9.0, y=9.0)
path_b = PatrolWaypoints(name="SafePath", waypoints=[(5,7), (7,9), (9,9)])
root.add_children([path_a, path_b])
```

### Pattern 4: Sense � Decide � Act
```python
root = py_trees.composites.Sequence(name="Adaptive", memory=True)
sense = GetPose(name="CheckPosition", blackboard_key='start')
decide = CheckBounds(name="InSafeZone", min_x=2.0, max_x=9.0)
act = GoToPose(name="MoveToGoal", x=5.0, y=5.0)
root.add_children([sense, decide, act])
```

---

## Turtlesim Constraints

**Workspace**: 11x11 units (0 to 11 on both axes)
- Default spawn: (5.544445, 5.544445)
- Recommended safe bounds: x=[1.0, 10.0], y=[1.0, 10.0]
- Going outside causes wrapping or failures

**Colors**: RGB values 0-255
- Red: (255, 0, 0)
- Green: (0, 255, 0)
- Blue: (0, 0, 255)
- Yellow: (255, 255, 0)
- Purple: (128, 0, 128)
- White: (255, 255, 255)

**Angles**: Radians (0 to 2�)
- 0: East (right)
- �/2: North (up)
- �: West (left)
- 3�/2: South (down)

---

## Validation Checklist

Before saving a generated BT, verify:

1. **Required imports present**
   - `import py_trees`
   - `from py_trees_nodes.primitives import ...`
   - `from py_trees_nodes.composites import ...`

2. **create_root() function exists**
   - Takes no arguments
   - Returns a py_trees.behaviour.Behaviour

3. **All coordinates in bounds**
   - x, y values between 0-11
   - Preferably 1-10 for safety

4. **All actions have unique names**
   - No duplicate node names in the tree

5. **Composites have children**
   - Sequence/Selector/Parallel nodes must have 1+ children

6. **Color values valid**
   - RGB values between 0-255

---

## Using ROS-MCP Tools

When generating BTs, you can verify actions exist using MCP tools:

```bash
# Check available topics
get_topics()  # Should see /turtle1/cmd_vel, /turtle1/pose

# Check available services
get_services()  # Should see /turtle1/set_pen
```

---

## Example: Complete Behavior Tree

### Task: "Draw a blue square and then patrol around it"

```python
"""
Behavior tree to draw a blue square and patrol around its perimeter.
"""

import py_trees
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from py_trees_nodes.primitives import GoToPose, SetPen
from py_trees_nodes.composites import DrawShape, PatrolWaypoints


def create_root() -> py_trees.behaviour.Behaviour:
    """
    Create BT: Draw blue square � Patrol around it

    Returns:
        Root node of the behavior tree
    """

    # Main sequence: do drawing first, then patrol
    root = py_trees.composites.Sequence(
        name="DrawAndPatrol",
        memory=True
    )

    # Step 1: Draw a blue square
    draw_square = DrawShape(
        name="DrawBlueSquare",
        shape_type='square',
        size=4.0,
        center_x=5.5,
        center_y=5.5,
        color=(69, 86, 255),  # Blue
        width=3
    )

    # Step 2: Patrol around the square
    # Square corners at (3.5, 3.5), (7.5, 3.5), (7.5, 7.5), (3.5, 7.5)
    patrol = PatrolWaypoints(
        name="PatrolSquare",
        waypoints=[
            (3.5, 3.5),  # Bottom-left
            (7.5, 3.5),  # Bottom-right
            (7.5, 7.5),  # Top-right
            (3.5, 7.5),  # Top-left
        ],
        loop=True  # Return to start
    )

    # Add both to sequence
    root.add_children([draw_square, patrol])

    return root


if __name__ == '__main__':
    print("Creating DrawAndPatrol behavior tree...")
    root = create_root()
    print("\nTree structure:")
    print(py_trees.display.unicode_tree(root, show_status=True))
    print("\nTo execute:")
    print("    python execution/run_bt.py generated_bts/draw_and_patrol.py")
```

---

## Best Practices

1. **Name nodes descriptively** - Use names that explain what the node does
2. **Keep trees shallow** - Prefer 2-3 levels deep over deeply nested trees
3. **Use composites when logical** - DrawShape and PatrolWaypoints are cleaner than many GoToPose
4. **Add safety checks** - Use CheckBounds before risky movements
5. **Comment complex logic** - Explain non-obvious tree structures
6. **Test incrementally** - Build and test simple trees before complex ones

---

## Generating a BT: Step-by-Step

1. **Parse user request** - Identify the goal
2. **Break into subtasks** - What actions are needed?
3. **Choose composition** - Sequence (ordered), Selector (fallback), Parallel (concurrent)
4. **Select actions** - Use primitives or composites from library
5. **Set parameters** - Coordinates, colors, sizes
6. **Build tree structure** - Create root, add children
7. **Validate** - Check syntax, bounds, logic
8. **Save to file** - Use descriptive filename in generated_bts/

---

## Error Handling

**Common Issues**:

- **Out of bounds**: Keep x,y in [1,10] range
- **Missing imports**: Include all used node types
- **Empty composites**: Sequences/Selectors need children
- **Invalid colors**: RGB must be 0-255
- **No create_root()**: Must be defined and return a node

**Debugging**: Users can run:
```bash
python validation/syntax_checker.py generated_bts/my_bt.py
python validation/ros_checker.py generated_bts/my_bt.py
```

---

## Advanced: Using Blackboard

The blackboard is py_trees' shared memory for inter-node communication.

**Writing to blackboard**:
```python
# GetPose writes to blackboard
get_pose = GetPose(name="SensePosition", blackboard_key='robot_pose')
```

**Reading from blackboard** (in custom nodes):
```python
blackboard = py_trees.blackboard.Client(name="MyNode")
blackboard.register_key(key='robot_pose', access=py_trees.common.Access.READ)
pose = blackboard.get('robot_pose')
```

For this MVP, blackboard usage is optional but available.

---

## Summary

To generate a behavior tree:
1. Understand the task
2. Choose appropriate actions from the library
3. Compose them with Sequence/Selector/Parallel
4. Set correct parameters (positions, colors, etc.)
5. Follow the file template
6. Validate and save

The generated BT will be executed with:
```bash
python execution/run_bt.py generated_bts/your_bt_name.py
```
