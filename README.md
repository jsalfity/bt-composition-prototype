# BT Composition Prototype for ROS Turtlesim

A research prototype for autonomous behavior tree (BT) composition using py_trees with ROS2 Turtlesim. This system enables an AI agent (Claude) to generate executable behavior trees from natural language descriptions.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Claude Skills Setup](#claude-skills-setup)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Available Actions](#available-actions)
- [Usage Guide](#usage-guide)
- [Validation](#validation)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

This prototype demonstrates AI-driven behavior tree composition with validation:

1. **Claude Skills** - bt-composer, bt-validator, bt-action-discovery
2. **Action library** - Primitive and compositional nodes for turtlesim control
3. **Validation tools** - 3-tier validation (syntax, parameters, semantics)
4. **Execution engine** - Run behavior trees with py_trees + ROS

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER REQUEST                                │
│                    "Draw a red circle"                               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        CLAUDE CODE                                   │
│                   (Invokes bt-composer skill)                        │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BT-COMPOSER SKILL                                 │
│                  (~/.claude/skills/bt-composer/)                     │
│                                                                      │
│  Step 1: Discover Actions                                           │
│    ├─> Invokes: bt-action-discovery skill (~/.claude/skills/)      │
│    │     └─> Reads: ./action_library/action_library.yaml            │
│    └─> Returns: Available actions & constraints                     │
│                                                                      │
│  Step 2: Generate BT                                                 │
│    └─> Creates: generated_bts/draw_red_circle.py                    │
│                                                                      │
│  Step 3: Validate                                                    │
│    └─> Runs: python validation/orchestrator.py <file>               │
│          ├─> validation/syntax_checker.py (Tier 1: Critical)        │
│          ├─> validation/ros_checker.py (Tier 1: Critical)           │
│          ├─> Parameter checks (Tier 2: Important)                   │
│          └─> Semantic checks (Tier 3: Advisory)                     │
│                                                                      │
│  Step 4: Handle Results                                              │
│    ├─> Tier 1 Fail? Regenerate (max 3x)                             │
│    └─> All Pass? Present to user                                    │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         EXECUTION                                    │
│    python execution/run_bt.py generated_bts/draw_red_circle.py      │
│                           │                                          │
│                           ▼                                          │
│                   ROS2 Turtlesim                                     │
│                  (via rosbridge:9090)                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Relationships

```
~/.claude/skills/              Project Repository
┌────────────────────┐        ┌──────────────────────────────────────┐
│  bt-action-        │        │  action_library/action_library.yaml  │
│  discovery/        │◄───────│  (robot-specific actions)             │
│  (generic)         │  reads │                                       │
├────────────────────┤        │                                       │
│  bt-composer/      │        │  validation/   (Python tools)        │
│  (generic)         │───────►│    ├─ orchestrator.py                │
│                    │ invokes│    ├─ syntax_checker.py              │
├────────────────────┤        │    ├─ structural_checker.py          │
│  bt-validator/     │        │    └─ ros_checker.py                 │
│  (generic)         │───────►│                                       │
│                    │ invokes│  generated_bts/   (AI-generated)     │
└────────────────────┘        │    └─ *.py                           │
                              └──────────────────────────────────────┘
```

---

## Prerequisites

### Required

- **Python 3.10+**
- **Docker** (for ROS2 Turtlesim with rosbridge)
- **Claude Code** (for AI-driven BT generation)

### Python Packages

```bash
pip install -r requirements.txt
```

Includes:
- `py_trees>=2.2.0` - Behavior tree library
- `roslibpy>=1.5.0` - ROS communication via websocket
- `pyyaml>=6.0` - Configuration files

---

## Installation

### 1. Clone Repository

```bash
git clone <repo-url>
cd bt-composition-prototype
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start ROS2 Turtlesim with Rosbridge

Ensure rosbridge_server is accessible at `localhost:9090`.

```bash
docker run -p 9090:9090 <your-turtlesim-image>
```

### 4. Verify ROS Connection

```bash
python -c "from execution.ros_connection import check_ros_connection; print('ROS OK' if check_ros_connection() else 'ROS FAILED')"
```

Expected output: `ROS OK`

---

## Claude Skills Setup

This project uses Claude Skills for AI-driven BT generation. Three generic skills must be installed in your user skills directory.

### Install Generic Skills

Copy the generic skills to `~/.claude/skills/` (Recommended):

```bash
# From your local copy of the skills
cp -r bt-composition-prototype/skills/bt-action-discovery ~/.claude/skills/
cp -r bt-composition-prototype/skills/bt-composer ~/.claude/skills/
cp -r bt-composition-prototype/skills/bt-validator ~/.claude/skills/
```

Or create symlinks (This doesn't work as well, still debugging):

```bash
ln -s bt-composition-prototype/skills/bt-action-discovery ~/.claude/skills/bt-action-discovery
ln -s bt-composition-prototype/skills/bt-composer ~/.claude/skills/bt-composer
ln -s bt-composition-prototype/skills/bt-validator ~/.claude/skills/bt-validator
```

### Verify Installation

Check that skills are available:

```bash
ls ~/.claude/skills/
# Should show: bt-action-discovery  bt-composer  bt-validator
```

### User-Level Skills

All three skills are now **user-level** skills in `~/.claude/skills/`:
- `bt-composer` - Generic BT generation logic
- `bt-validator` - Generic validation logic
- `bt-action-discovery` - Generic action discovery (reads from project's `action_library/action_library.yaml`)

The skills are **generic and reusable** across any robotics project. The **action library** is **project-specific** and defines what actions are available for each robot/environment.

---

## Quick Start

### 1. Set Up Claude Skills

Follow [Claude Skills Setup](#claude-skills-setup) above.

### 2. Run a Manual Example

Test the system with a hand-crafted example:

```bash
python execution/run_bt.py bt_library/manual_examples/draw_square.py
```

You should see:
- Tree structure printed
- Tick-by-tick execution log
- Turtle drawing a blue square

### 3. Generate BT with Claude

Ask Claude Code:
```
"Generate a behavior tree to draw a red circle"
```

Claude will:
1. Invoke bt-composer skill
2. Discover available actions
3. Generate `generated_bts/draw_red_circle.py`
4. Validate the BT
5. Present execution command

### 4. Execute Generated BT

```bash
python execution/run_bt.py generated_bts/draw_red_circle.py
```

---

## Project Structure

```
bt-composition-prototype/
├── README.md                   # This file
├── requirements.txt            # Python dependencies
│
├── action_library/             # Robot/environment-specific actions
│   └── action_library.yaml    # Action definitions & ROS dependencies
│
├── validation/                 # BT validation tools
│   ├── orchestrator.py         # 3-tier validation coordinator
│   ├── syntax_checker.py       # Tier 1: Syntax & structure
│   ├── structural_checker.py   # Tier 2: Structural validation
│   └── ros_checker.py          # Tier 1: Action existence
│
├── bt_library/                 # Hand-crafted baseline BTs
│   └── manual_examples/
│       ├── draw_square.py
│       └── patrol_waypoints.py
│
├── generated_bts/              # AI-generated BTs (gitignored)
│   └── .gitkeep
│
├── py_trees_nodes/             # BT node implementations
│   ├── primitives/             # Atomic actions
│   │   ├── goto_pose.py
│   │   ├── set_pen.py
│   │   ├── move_distance.py
│   │   ├── get_pose.py
│   │   └── check_bounds.py
│   └── composites/             # Compositional actions
│       ├── draw_shape.py
│       └── patrol_waypoints.py
│
├── execution/                  # BT execution engine
│   ├── run_bt.py              # Main executor
│   └── ros_connection.py      # Rosbridge connection
│
└── tests/                      # Tests
    └── ...
```

---

## Available Actions

### Primitive Actions

| Action | Purpose | Parameters |
|--------|---------|------------|
| **GoToPose** | Navigate to position | `x, y, theta, tolerance_pos, tolerance_angle` |
| **SetPen** | Configure pen | `r, g, b, width, off` |
| **PenUp** | Disable drawing | - |
| **PenDown** | Enable drawing | `r, g, b, width` |
| **MoveDistance** | Move fixed distance | `distance, speed` |
| **GetPose** | Read position | `blackboard_key` |
| **CheckBounds** | Verify safe zone | `min_x, max_x, min_y, max_y` |

### Compositional Actions

| Action | Purpose | Parameters |
|--------|---------|------------|
| **DrawShape** | Draw circle/square/triangle | `shape_type, size, center_x, center_y, color, width` |
| **PatrolWaypoints** | Navigate multiple waypoints | `waypoints, loop` |

### Workspace Constraints

- **Coordinates**: x=[0,11], y=[0,11]
- **Safe zone** (recommended): x=[1,10], y=[1,10]
- **Colors**: RGB values [0-255]
- **Default spawn**: (5.544445, 5.544445)

See `action_library/action_library.yaml` for complete reference.

---

## Usage Guide

### Option 1: AI-Generated BTs (Recommended)

Ask Claude Code:
```
"Draw a blue square with side length 3"
```

Claude will invoke `bt-composer` skill and:
1. Discover available actions
2. Generate Python BT file
3. Validate (3-tier validation)
4. Present execution command

### Option 2: Manual BT Creation

Create a Python file following this structure:

```python
import py_trees
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from py_trees_nodes.primitives import GoToPose, SetPen
from py_trees_nodes.composites import DrawShape


def create_root() -> py_trees.behaviour.Behaviour:
    """Create the behavior tree root node."""

    root = py_trees.composites.Sequence(name="MyTask", memory=True)

    # Add your actions
    circle = DrawShape(
        name="Circle",
        shape_type="circle",
        size=2.0,
        center_x=5.5,
        center_y=5.5,
        color=(255, 0, 0),
        width=3
    )

    root.add_children([circle])
    return root


if __name__ == '__main__':
    print("Creating behavior tree...")
    root = create_root()
    print(py_trees.display.unicode_tree(root, show_status=True))
```

### Execute BT

```bash
python execution/run_bt.py path/to/your_bt.py
```

---

## Validation

### 3-Tier Validation System

**Tier 1: Critical (Must Pass)**
- Valid Python syntax
- `create_root()` function exists and returns `py_trees.behaviour.Behaviour`
- All imports available
- All actions exist in action library
- Proper sys.path setup for module imports

**Tools:** `validation/syntax_checker.py`, `validation/ros_checker.py`

**Tier 2: Structural (Should Pass)**
- No duplicate node names within tree
- `memory=True` parameter set on Sequence/Selector composites
- Proper tree structure and node relationships

**Tools:** `validation/structural_checker.py`

**Tier 3: Semantic (Reserved for Future)**
- Semantic validation using LLM-as-judge
- Action ordering reasonableness
- Task completion verification
- Best practice adherence

**Tools:** Future implementation

### Run Validation

```bash
# Full validation (all tiers)
python validation/orchestrator.py generated_bts/my_bt.py

# Individual validators
python validation/syntax_checker.py generated_bts/my_bt.py
python validation/ros_checker.py generated_bts/my_bt.py
python validation/structural_checker.py generated_bts/my_bt.py
```

**Note:** Claude automatically validates during BT generation.

---

## Examples

### Example 1: Draw a Square

```bash
python execution/run_bt.py bt_library/manual_examples/draw_square.py
```

**What it does:**
- Sets pen to red
- Navigates to 5 corners to draw a 2x2 square

### Example 2: Patrol Waypoints

```bash
python execution/run_bt.py bt_library/manual_examples/patrol_waypoints.py
```

**What it does:**
- Reads current position
- Checks bounds
- Patrols through 4 waypoints
- Returns to start

### Example 3: AI-Generated

Ask Claude:
```
"Draw a smiley face"
```

Claude will generate a BT using composite actions and patterns.

---

## Troubleshooting

### "Failed to connect to ROS"

**Solution:**
- Verify rosbridge: `curl http://localhost:9090`
- Check Docker container is running
- Ensure port 9090 is accessible

### "Skill not found: bt-composer"

**Solution:**
- Install skills: See [Claude Skills Setup](#claude-skills-setup)
- Verify: `ls ~/.claude/skills/` shows `bt-composer` and `bt-validator`

### "Validation failed"

**Solution:**
- Check validation output for specific errors
- See validation-reference.md in bt-validator skill for error catalog
- Ask Claude to debug: "Validate my_bt.py and fix errors"

### "Turtle not moving"

**Solution:**
- Verify turtlesim is running in ROS
- Check `/turtle1/cmd_vel` topic exists
- Reset turtle if stuck: Use ROS service call

---

## Resources

- **py_trees documentation**: https://py-trees.readthedocs.io/
- **ROS2 Turtlesim**: https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Introducing-Turtlesim/Introducing-Turtlesim.html
- **roslibpy**: https://roslibpy.readthedocs.io/
- **Claude Code**: https://claude.com/claude-code

---

## Team Setup

For team members:

1. **Clone repository**
   ```bash
   git clone <repo-url>
   cd bt-composition-prototype
   pip install -r requirements.txt
   ```

2. **Install Claude Skills**
   ```bash
   # Copy shared skills from this repository
   cp -r bt-composition-prototype/skills/bt-action-discovery ~/.claude/skills/
   cp -r bt-composition-prototype/skills/bt-composer ~/.claude/skills/
   cp -r bt-composition-prototype/skills/bt-validator ~/.claude/skills/
   ```

3. **Start ROS environment**
   ```bash
   docker run -p 9090:9090 <turtlesim-image>
   ```

4. **Test**
   ```bash
   python execution/run_bt.py bt_library/manual_examples/draw_square.py
   ```

---

**Built with**: py_trees, roslibpy, ROS2, Claude AI
