# Pick and place with gripper

## Prerequisite

Having completed [tutorial 6](../tutorial_6/README.md).

## Overview

Tutorial 6 executed one arm trajectory with `send_trajectory`. This tutorial
adds the gripper: the robot must open the fingers before approaching the box,
close them before transport, then open them again at the goal.

The script plans a pick-and-place path with an HPP manipulation constraint
graph. We then use `hpp_exec` to split the path at grasp and release
transitions and execute each segment on Gazebo.

For the full `hpp_exec` API, see the
[hpp-exec documentation](https://gepetto.github.io/doc/hpp-exec/doxygen-html/index.html).

## Setting up the simulation

Use the same Docker image as tutorial 6 (`hpp-ros2:tuto`). If you have not
built it yet, see the [tutorial 6 instructions](../tutorial_6/README.md).

Inside the container, build the packages (first time only):

```
cd ~/devel/src
make hpp-exec.install
make hpp_tutorial.install
```

## Terminal 1: Launching the simulation

Launch Gazebo with the FR3 and its gripper:

```
ros2 launch hpp_tutorial tutorial_7_launch.py
```

Wait until you see `Configured and activated gripper_controller` in the output.

Note: one gripper finger may appear loose in Gazebo. This is a simulation
artefact with mimic joints. It does not affect the tutorial.

## Terminal 2: Planning

Open a second terminal:

```
docker exec -it hpp bash
```

Run the tutorial script:

```
cd ~/devel/src/hpp_tutorial/tutorial_7
python -i init.py
```

The script loads the FR3, the ground, and a box. It solves a pick-and-place
problem that moves the box from `(0.4, -0.2)` to `(0.4, 0.2)`, optimizes the
path, and time-parameterizes it with `SimpleTimeParameterization`.

You can visualize the planned path in the browser viewer:

```python
v = display()
v.loadPath(p_timed)
```

At this point the useful objects are:

- `configs`: sampled HPP configurations along the timed path.
- `times`: timestamps in seconds.
- `graph`: the HPP manipulation constraint graph.
- `open_gripper` and `close_gripper`: small Gazebo gripper actions.

## Building execution segments

The planned path contains the approach, transport, and retreat motion in one
path. To execute it, split it where the manipulation graph changes state:

```python
from hpp_exec import segments_from_graph

segments = segments_from_graph(
    configs, times, graph,
    on_grasp=close_gripper,
    on_release=open_gripper,
)
```

For this problem, `segments` contains three phases:

| # | Phase     | What the arm does           | Pre-action |
|---|-----------|-----------------------------|------------|
| 0 | approach  | move above the box, descend | none       |
| 1 | transport | carry the box to the goal   | close      |
| 2 | retreat   | lift and return             | open       |

Make the initial gripper state explicit before the approach:

```python
segments[0].pre_actions.insert(0, open_gripper)
```

This matters if a previous run left the simulated gripper closed.

## Executing the segments

Send the arm segments to the arm controller and let the pre-actions command
the gripper controller:

```python
from hpp_exec import execute_segments

execute_segments(
    segments, configs, times,
    joint_names=[f"fr3_joint{i}" for i in range(1, 8)],
    joint_indices=list(range(7)),
)
```

You should see the fingers open, the arm descend, the fingers close on the
box, the arm carry the box to the goal, the fingers open, and the arm retreat.

`init.py` also defines this convenience wrapper:

```python
execute_on_gazebo()
```

## Experiment

Inspect the segments before executing:

```python
for i, s in enumerate(segments):
    pre = [a.__name__ for a in s.pre_actions]
    print(f"segment {i}: configs[{s.start_index}:{s.end_index}] pre={pre}")
```

Try running the execution twice without resetting the box pose. On the second
run, the planned start pose and the simulated world no longer match, so the
robot will descend where the box used to be. `hpp_exec` executes the path that
HPP planned, but it does not re-plan against the current world state.
