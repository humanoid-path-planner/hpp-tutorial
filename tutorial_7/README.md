# Pick and place with gripper

## Prerequisite

Having completed [tutorial 6](../tutorial_6/README.md).

## Overview

Tutorial 6 executed a single arm trajectory. Pick-and-place adds a second
actuator — the gripper — whose state must change **in the middle** of the
path: open on approach, closed during transport, open again after release.

This tutorial builds an HPP manipulation constraint graph, solves a
pick-and-place problem, splits the resulting path into **segments** delimited
by grasp/release events detected from the graph, and executes the segments on
Gazebo with gripper actions in between.

## Setting up the simulation

Use the same Docker image as tutorial 6 (`hpp-ros2:tuto`). If you haven't built
it yet, see the [tutorial 6 instructions](../tutorial_6/README.md).

Inside the container, build the packages (first time only):

```
cd ~/devel/src
make hpp-exec.install
make hpp_tutorial.install
```

## Terminal 1: Launching the simulation

Launch Gazebo with the FR3 including its gripper:

```
ros2 launch hpp_tutorial tutorial_7_launch.py
```

Wait until you see `Configured and activated gripper_controller` in the output.

Note: one gripper finger may appear loose in Gazebo. This is a simulation
artefact with mimic joints (finger2 copies finger1 via physics constraints).
It does not affect the real robot.

## Terminal 2: Planning and executing

Open a second terminal:

```
docker exec -it hpp bash
```

Run the tutorial script:

```
cd ~/devel/src/hpp_tutorial/tutorial_7
python -i init.py
```

The script loads the FR3 with a box on a ground plane, builds a manipulation
constraint graph, and solves a pick-and-place problem (move the box from
`(0.4, -0.2)` to `(0.4, 0.2)`). At the end you get two lists, `configs` and
`times`, describing the full planned motion — including the waypoints where a
grasp is acquired or released.

You can visualize the path in the browser viewer:
```python
v = display()
v.loadPath(p_timed)
```

## Understanding the phases

HPP returns a single continuous path, but the robot cannot execute it as one
trajectory: the gripper has to close somewhere in the middle and open again
later. We need to break the path at those events.

For this pick-and-place there are exactly two such events — one pick, one
place — which split the path into three phases:

| # | Phase      | What the arm does           | Gripper action before |
|---|------------|-----------------------------|-----------------------|
| 0 | approach   | move above the box, descend | open (see below)      |
| 1 | transport  | carry the box to the goal   | close                 |
| 2 | retreat    | lift and return             | open                  |

## Detecting grasp/release events

HPP's constraint graph already knows where those events are. Each configuration
belongs to a graph **state** whose name lists the active grasps (e.g. `"free"`
or `"fr3/gripper grasps box/handle"`). `hpp_exec` walks the configs, calls
`graph.getStateFromConfiguration(q)` at each one, and flags every index where
the active-grasp set changes:

```python
from hpp_exec import extract_grasp_transitions

for t in extract_grasp_transitions(configs, times, graph):
    print(f"t={t.time:.2f}s  acquired={t.acquired}  released={t.released}")
```

## Building segments from the constraint graph

`segments_from_graph()` uses those transitions to build one `Segment` per
phase, wiring `on_grasp` and `on_release` as *pre-actions* on the appropriate
segments:

```python
from hpp_exec import segments_from_graph

segments = segments_from_graph(
    configs, times, graph,
    on_grasp=close_gripper,
    on_release=open_gripper,
)
```

For this problem you get three segments matching the table above: segment 0
has no pre-action, segment 1 closes the gripper first, segment 2 opens it.

## Sync the initial gripper state

`segments_from_graph()` only sets pre-actions on segments *after* a transition,
so segment 0 has none. But segment 0 is precisely where the arm descends
toward the box, and HPP planned that descent assuming the fingers are already
open (see `q_init` in `init.py`). If the real gripper is closed — for instance
because the previous run ended mid-transport, or Gazebo spawned with fingers
at some other pose — the arm descends into the box.

The fix is one line: prepend the open action to segment 0's pre-actions. Since
`send_trajectory` blocks until the gripper controller reports completion, the
arm will not move until the fingers are actually open:

```python
segments[0].pre_actions.insert(0, open_gripper)
```

## Executing with gripper actions

Gripper actions are just callables returning `True` on success — here we send
a small two-point trajectory to the gripper controller. Only
`fr3_finger_joint1` is commanded; `fr3_finger_joint2` follows as a mimic joint.

```python
from hpp_exec import segments_from_graph, execute_segments, send_trajectory
import numpy as np

def open_gripper():
    return send_trajectory(
        [np.array([0.0]), np.array([0.035])],
        [0.0, 0.5],
        joint_names=['fr3_finger_joint1'],
        controller_topic='/gripper_controller/follow_joint_trajectory',
    )

def close_gripper():
    return send_trajectory(
        [np.array([0.035]), np.array([0.0])],
        [0.0, 0.5],
        joint_names=['fr3_finger_joint1'],
        controller_topic='/gripper_controller/follow_joint_trajectory',
    )

segments = segments_from_graph(
    configs, times, graph,
    on_grasp=close_gripper,
    on_release=open_gripper,
)
segments[0].pre_actions.insert(0, open_gripper)

execute_segments(
    segments, configs, times,
    joint_names=[f'fr3_joint{i}' for i in range(1, 8)],
    joint_indices=list(range(7)),
)
```

`execute_segments()` iterates over the segments: for each one it runs every
`pre_action` (aborting on the first `False`), sends the arm trajectory for
`configs[start:end]` and waits for it to complete, then runs every
`post_action`.

Expected behaviour in Gazebo: the fingers open, the arm descends, the fingers
close on the box, the arm carries it to the goal, the fingers open, the arm
retreats.

## Reference: Franka native gripper (real robot)

On a real Franka robot you can use the native gripper actions, which provide
force-controlled grasping via `franka_msgs`. Drop-in replacement: swap the
`open_gripper`/`close_gripper` callables for `gripper.open`/`gripper.close`.

```python
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from franka_msgs.action import Grasp, Move

class FrankaGripper:
    def __init__(self, arm_id="fr3"):
        self.arm_id = arm_id
        if not rclpy.ok():
            rclpy.init()
        self._node = Node("franka_gripper")
        self._grasp_client = ActionClient(
            self._node, Grasp, f"/{arm_id}_gripper/grasp"
        )
        self._move_client = ActionClient(
            self._node, Move, f"/{arm_id}_gripper/move"
        )

    def open(self) -> bool:
        """Open gripper using Move action (position control)."""
        if not self._move_client.wait_for_server(timeout_sec=10.0):
            return False
        goal = Move.Goal()
        goal.width = 0.08  # Fully open (meters)
        goal.speed = 0.05  # m/s
        future = self._move_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self._node, future, timeout_sec=10.0)
        goal_handle = future.result()
        if not goal_handle or not goal_handle.accepted:
            return False
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self._node, result_future, timeout_sec=30.0)
        return True

    def close(self) -> bool:
        """Close gripper using Grasp action (force-controlled)."""
        if not self._grasp_client.wait_for_server(timeout_sec=10.0):
            return False
        goal = Grasp.Goal()
        goal.width = 0.02          # Target width (meters)
        goal.speed = 0.05          # Closing speed (m/s)
        goal.force = 50.0          # Grasping force (Newtons)
        goal.epsilon.inner = 0.01  # Tolerance for grasp success
        goal.epsilon.outer = 0.01
        future = self._grasp_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self._node, future, timeout_sec=10.0)
        goal_handle = future.result()
        if not goal_handle or not goal_handle.accepted:
            return False
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self._node, result_future, timeout_sec=30.0)
        return True

    def destroy(self):
        self._node.destroy_node()

gripper = FrankaGripper("fr3")
segments = segments_from_graph(
    configs, times, graph,
    on_grasp=gripper.close,
    on_release=gripper.open,
)
segments[0].pre_actions.insert(0, gripper.open)  # sync initial state
execute_segments(segments, configs, times, ...)
gripper.destroy()
```
