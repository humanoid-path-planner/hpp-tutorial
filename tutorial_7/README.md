# Pick and place with gripper

## Prerequisite

Having completed [tutorial 6](../tutorial_6/README.md).

## Overview

This tutorial extends tutorial 6 to a full pick-and-place scenario. It loads the
FR3 robot with a gripper, a box, and a ground plane, builds a manipulation
constraint graph, solves the pick-and-place problem, and executes on Gazebo with
gripper open/close actions between trajectory segments.

## Setting up the simulation

Use the same Docker image as tutorial 6 (`hpp-tutorial-ros2`). If you haven't
built it yet, see the [tutorial 6 instructions](../tutorial_6/README.md).

Inside the container, build the packages (first time only):

```
cd ~/devel/src
make hpp-exec.install
make hpp_tutorial.install
```

## Terminal 1: Launching the simulation

Source the environments, then launch Gazebo with the FR3 including its gripper:

```
source /opt/ros/jazzy/setup.bash
source /opt/franka_ws/install/setup.bash
source ~/devel/config.sh
ros2 launch ~/devel/install/share/hpp_tutorial/tutorial_7/launch_sim.py
```

Wait until you see `Configured and activated gripper_controller` in the output.

Note: One gripper finger may appear loose in Gazebo. This is a simulation artifact
with mimic joints (finger2 copies finger1 via physics constraints). It does not
affect the real robot.

## Terminal 2: Planning and executing

Open a second terminal:

```
docker exec -it hpp bash
```

Source the environments and run the tutorial script:

```
source /opt/ros/jazzy/setup.bash
source /opt/franka_ws/install/setup.bash
source ~/devel/config.sh
cd ~/devel/src/hpp_tutorial/tutorial_7
python -i init.py
```

The script loads the FR3 robot with a box on a ground plane, builds a
manipulation constraint graph, and solves a pick-and-place problem (moving the
box from one position to another). The result is a list of `configs` and `times`
with grasp/release transitions embedded in the path.

You can visualize the path in the viewer:
```python
v = display()
v.loadPath(p_timed)
```

## Understanding segments and actions

The key difference from tutorial 6 is that the trajectory has multiple phases:
approach, grasp, transport, and release. The `hpp_exec` package detects these
transitions from the constraint graph and splits the trajectory into **segments**
with gripper actions between them.

### How it works

HPP's constraint graph encodes the grasp state at each configuration. The
`segments_from_graph()` function queries the graph for each waypoint to detect
when a grasp is acquired or released:

```python
from hpp_exec import extract_grasp_transitions

transitions = extract_grasp_transitions(configs, times, graph)
for t in transitions:
    print(f"Config {t.config_index} at t={t.time:.2f}s:")
    print(f"  Acquired: {t.acquired}")  # New grasps (close gripper)
    print(f"  Released: {t.released}")  # Lost grasps (open gripper)
```

### Segments and pre_actions

A `Segment` represents a slice of the trajectory with optional actions to run
before or after sending that segment:

```python
from hpp_exec import Segment

# Example: 3 segments for approach → grasp → retreat
segments = [
    Segment(0, 50),                           # Approach (no action)
    Segment(50, 150, pre_actions=[close_gripper]),  # Transport (close first)
    Segment(150, 200, pre_actions=[open_gripper]),  # Retreat (open first)
]
```

The `execute_segments()` function iterates through segments:
1. Run all `pre_actions` (stop if any returns False)
2. Send the arm trajectory for this segment
3. Run all `post_actions` (stop if any returns False)

## Executing with gripper actions

Define gripper actions as functions returning `True` on success:

```python
from hpp_exec import segments_from_graph, execute_segments, send_trajectory
import numpy as np

# Only fr3_finger_joint1 is controllable (finger2 is a mimic joint)
def close_gripper():
    send_trajectory(
        [np.array([0.035]), np.array([0.0])],
        [0.0, 0.5],
        joint_names=['fr3_finger_joint1'],
        controller_topic='/gripper_controller/follow_joint_trajectory',
    )
    return True

def open_gripper():
    send_trajectory(
        [np.array([0.0]), np.array([0.035])],
        [0.0, 0.5],
        joint_names=['fr3_finger_joint1'],
        controller_topic='/gripper_controller/follow_joint_trajectory',
    )
    return True

# Build segments from the constraint graph (auto-detects grasp/release)
segments = segments_from_graph(
    configs, times, graph,
    on_grasp=close_gripper,
    on_release=open_gripper,
)

# Execute all segments with gripper actions
execute_segments(
    segments, configs, times,
    joint_names=[f'fr3_joint{i}' for i in range(1, 8)],
    joint_indices=list(range(7)),
)
```

You should see the robot approach the box, close its gripper, move the box to
the goal position, open the gripper, and retreat.

## Reference: Franka native gripper (real robot)

On a real Franka robot, you can use the native gripper actions which provide
force-controlled grasping via `franka_msgs`:

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

# Usage with segments
gripper = FrankaGripper("fr3")
segments = segments_from_graph(
    configs, times, graph,
    on_grasp=gripper.close,
    on_release=gripper.open,
)
execute_segments(segments, configs, times, ...)
gripper.destroy()
```
