# BT Composition Prototype for ROS Turtlesim

A minimal viable prototype for autonomous behavior tree (BT) composition using py_trees with ROS2 Turtlesim. This system enables an AI agent (Claude) to generate executable behavior trees from natural language descriptions.

**Phase 1 Status**: MVP Complete - Manual execution, baseline functionality

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Available Actions](#available-actions)
- [Usage Guide](#usage-guide)
- [Validation](#validation)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## Overview

This prototype demonstrates:

1. **Manual behavior trees** - Hand-crafted baseline examples
2. **Action library** - Primitive and compositional nodes for turtlesim control
3. **Execution engine** - Run behavior trees with py_trees
4. **Validation tools** - Syntax and ROS dependency checking
5. **Claude skill** - Enable AI agent to generate behavior trees

### Architecture

```
User Request → Claude (uses SKILL.md) → Generated BT (.py)
                                              ↓
                                    Validation (optional)
                                              ↓
                                         Execution
                                              ↓
                                    ROS2 Turtlesim (via rosbridge)
```

---

## Prerequisites

### Required

- **Python 3.10+**
- **Docker** (for ROS2 Turtlesim with rosbridge)
- **ros-mcp-server** (for Claude to interact with ROS)

### Python Packages

Install via `requirements.txt`:
```bash
pip install -r requirements.txt
```

Includes:
- `py_trees>=2.2.0` - Behavior tree library
- `roslibpy>=1.5.0` - ROS communication via websocket
- `pyyaml>=6.0` - Configuration files

---

## Installation

### 1. Clone or Create Project

```bash
cd bt-composition-prototype
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start ROS2 Turtlesim with Rosbridge

Ensure your Docker container with ROS2 Turtlesim is running with rosbridge_server accessible at `localhost:9090`.

Example Docker command (adjust to your setup):
```bash
docker run -p 9090:9090 <your-turtlesim-image>
```

### 4. Verify ROS Connection

```bash
python -c "from execution.ros_connection import check_ros_connection; print('ROS OK' if check_ros_connection() else 'ROS FAILED')"
```

You should see: `ROS OK`

---

## Quick Start

### Run a Manual Example

Try the hand-crafted square drawing example:

```bash
python execution/run_bt.py bt_library/manual_examples/draw_square.py
```

You should see:
- Tree structure printed
- Tick-by-tick execution log
- Turtle drawing a blue square in the simulator

### Run Another Example

Try the patrol example:

```bash
python execution/run_bt.py bt_library/manual_examples/patrol_waypoints.py
```

---

## Project Structure

```
bt-composition-prototype/
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
│
├── skills/                     # Claude Skills (for MCP integration)
│   └── bt-composer/
│       ├── SKILL.md            # Main skill documentation for Claude
│       └── action_library.yaml # Catalog of available actions
│
├── bt_library/                 # Hand-crafted baseline behavior trees
│   ├── __init__.py
│   └── manual_examples/
│       ├── draw_square.py      # Example: Draw a square
│       └── patrol_waypoints.py # Example: Patrol between waypoints
│
├── generated_bts/              # Agent-generated BTs (gitignored)
│   ├── .gitkeep
│   └── README.md
│
├── py_trees_nodes/             # Behavior tree node implementations
│   ├── __init__.py
│   ├── base_action.py          # Base class for action nodes
│   ├── primitives/             # Atomic action nodes
│   │   ├── __init__.py
│   │   ├── goto_pose.py        # Navigate to position
│   │   ├── set_pen.py          # Control pen settings
│   │   ├── move_distance.py    # Move fixed distance
│   │   ├── get_pose.py         # Read current position (sensing)
│   │   └── check_bounds.py     # Verify in bounds (condition)
│   └── composites/             # Compositional action nodes
│       ├── __init__.py
│       ├── draw_shape.py       # Draw geometric shapes
│       └── patrol_waypoints.py # Visit multiple waypoints
│
├── validation/                 # BT validation utilities
│   ├── __init__.py
│   ├── syntax_checker.py       # Python AST validation
│   └── ros_checker.py          # ROS dependency checking
│
├── execution/                  # BT execution engine
│   ├── __init__.py
│   ├── run_bt.py              # Main executor script
│   └── ros_connection.py      # Rosbridge connection management
│
└── tests/                      # Tests (basic)
    ├── test_manual_bts.py
    └── test_nodes.py
```

---

## Available Actions

### Primitive Actions

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| **GoToPose** | Navigate to position | `x, y, theta` |
| **SetPen** | Configure pen | `r, g, b, width, off` |
| **PenUp** | Disable drawing | - |
| **PenDown** | Enable drawing | `r, g, b, width` |
| **MoveDistance** | Move fixed distance | `distance, speed` |
| **GetPose** | Read position (sensing) | `blackboard_key` |
| **CheckBounds** | Verify safe zone (condition) | `min_x, max_x, min_y, max_y` |

### Compositional Actions

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| **DrawShape** | Draw circle/square/triangle | `shape_type, size, center_x, center_y, color` |
| **PatrolWaypoints** | Navigate multiple waypoints | `waypoints, loop` |

### py_trees Composites

- **Sequence**: Execute children in order (AND logic)
- **Selector**: Try alternatives until success (OR logic)
- **Parallel**: Execute children concurrently

See `skills/bt-composer/action_library.yaml` for complete reference.

---

## Usage Guide

### 1. Create a Behavior Tree

**Option A: Manual Creation**

Create a Python file in `bt_library/manual_examples/`:

```python
import py_trees
from py_trees_nodes.primitives import GoToPose, SetPen

def create_root():
    root = py_trees.composites.Sequence(name="MyTask", memory=False)

    set_pen = SetPen(name="SetRed", r=255, g=0, b=0, width=3)
    move = GoToPose(name="Move", x=7.0, y=7.0)

    root.add_children([set_pen, move])
    return root
```

**Option B: Claude Generation**

1. Ensure Claude has access to the `bt-composer` skill
2. Ask Claude: "Generate a behavior tree to draw a triangle"
3. Claude will create a file in `generated_bts/`

### 2. Validate (Optional)

Check syntax:
```bash
python validation/syntax_checker.py path/to/your_bt.py
```

Check ROS dependencies:
```bash
python validation/ros_checker.py path/to/your_bt.py
```

### 3. Execute

```bash
python execution/run_bt.py path/to/your_bt.py
```

The script will:
- Connect to ROS (rosbridge at localhost:9090)
- Load and setup the behavior tree
- Execute with 10 Hz tick rate
- Display tree structure and status updates
- Timeout after 1000 ticks if not completed

---

## Validation

### Syntax Checker

Validates:
- Python syntax (AST parsing)
- Required imports present
- `create_root()` function exists
- Function returns a node

Usage:
```bash
python validation/syntax_checker.py generated_bts/my_bt.py
```

### ROS Checker

Validates:
- Action nodes are in library
- ROS topics/services required
- Optional: Live ROS availability check

Usage:
```bash
# Basic check
python validation/ros_checker.py generated_bts/my_bt.py

# With live ROS check
python validation/ros_checker.py generated_bts/my_bt.py --check-live
```

---

## Examples

### Example 1: Draw a Square

See `bt_library/manual_examples/draw_square.py`

**What it does**:
- Sets pen to blue
- Navigates to 5 corners to draw a 2x2 square

**Run**:
```bash
python execution/run_bt.py bt_library/manual_examples/draw_square.py
```

### Example 2: Patrol Waypoints

See `bt_library/manual_examples/patrol_waypoints.py`

**What it does**:
- Reads current position
- Checks bounds
- Patrols through 4 waypoints in a rectangle
- Returns to start

**Run**:
```bash
python execution/run_bt.py bt_library/manual_examples/patrol_waypoints.py
```

### Example 3: Using Compositional Nodes

```python
from py_trees_nodes.composites import DrawShape

def create_root():
    root = py_trees.composites.Sequence(name="DrawCircle", memory=False)

    circle = DrawShape(
        name="DrawGreenCircle",
        shape_type='circle',
        size=2.0,
        center_x=5.5,
        center_y=5.5,
        color=(0, 255, 0),
        width=3
    )

    root.add_child(circle)
    return root
```

---

## Troubleshooting

### Issue: "Failed to connect to ROS"

**Solution**:
- Verify rosbridge is running: `curl http://localhost:9090`
- Check Docker container is up
- Ensure port 9090 is not blocked

### Issue: "Turtle not moving"

**Solution**:
- Verify turtlesim node is running in ROS
- Check `/turtle1/cmd_vel` topic exists
- Ensure turtle hasn't hit bounds (reset with ROS service)

### Issue: "Syntax check failed"

**Solution**:
- Check Python syntax in generated file
- Ensure all imports are present
- Verify `create_root()` function exists

### Issue: "Behavior tree timeout"

**Solution**:
- Increase `max_ticks` in `run_bt.py` (default: 1000)
- Check if turtle is stuck (reset simulation)
- Verify target positions are reachable

---

## Next Steps

### Phase 2: Agent-Driven Generation

- Integrate with Claude via ros-mcp-server
- Automatic validation before execution
- Error feedback loop for regeneration

### Phase 3: Learning from Execution

- Capture execution traces
- Analyze success/failure patterns
- Refine action library based on outcomes

### Extensions

- Add more primitive actions (rotate, wait, etc.)
- Implement decorators (retry, timeout, etc.)
- Support for multiple turtles
- Real robot deployment (beyond turtlesim)

---

## Contributing

This is a research prototype. Suggested improvements:

1. **More action nodes** - Add domain-specific primitives
2. **Better validation** - Deeper semantic checks
3. **Execution monitoring** - Real-time visualization
4. **Error recovery** - Automatic retry strategies

---

## License

Research prototype - adjust as needed for your project.

---

## Resources

- **py_trees documentation**: https://py-trees.readthedocs.io/
- **ROS2 Turtlesim**: https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Introducing-Turtlesim/Introducing-Turtlesim.html
- **roslibpy**: https://roslibpy.readthedocs.io/

---

## Contact

For questions about this prototype, refer to the project documentation or consult the behavior tree skill file at `skills/bt-composer/SKILL.md`.

---

**Built with**: py_trees, roslibpy, ROS2, Claude AI
