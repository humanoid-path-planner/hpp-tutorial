# Pick and place with overlapping gripper opening

## Prerequisite

Having completed [tutorial 7](../tutorial_7/README.md).

## Overview

Tutorial 7 opens the gripper as a blocking pre-action before the approach
motion. This tutorial uses `hpp_exec.BackgroundAction` to start opening the
gripper in the background, let the arm begin travelling, then wait for the
opening action just before grasping the box.

The planning problem, Gazebo setup, and pick-and-place path are the same as in
tutorial 7. Only the execution actions change.

For the full `hpp_exec` API, see the
[hpp-exec documentation](https://gepetto.github.io/doc/hpp-exec/doxygen-html/index.html).

## Setting up the simulation

Use the same Docker image as tutorial 6 (`hpp-ros2:tuto`). If you have not
built it yet, see the [tutorial 6 instructions](../tutorial_6/README.md).

## Terminal 1: Launching the simulation

Launch Gazebo with the FR3 and its gripper:

```
ros2 launch hpp_tutorial tutorial_8_launch.py
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
cd ~/devel/src/hpp_tutorial/tutorial_8
python -i init.py
```

The script loads the FR3, the ground, and a box. It solves the same
pick-and-place problem as tutorial 7, optimizes the path, enforces transition
semantics, and time-parameterizes it with `SimpleTimeParameterization`.

You can visualize the planned path in the browser viewer:

```python
v = display()
v.loadPath(p_timed)
```

At this point the useful objects are:

- `p_timed`: the time-parameterized HPP path.
- `configs`: sampled HPP configurations along the timed path.
- `times`: timestamps in seconds, returned by `segments_from_graph`.
- `segments`: graph segments where you can add pre/post actions.
- `graph`: the HPP manipulation constraint graph.
- `open_gripper`, `close_gripper`, `grasp_box`, and `release_box`: Gazebo
  actions for the gripper and simulated box attachment.
- `background_open_gripper`: a `BackgroundAction` wrapping `open_gripper`.

## Building execution segments

The planned path contains the approach, transport, and retreat motion in one
path. Ask `hpp_exec` to sample the timed path and expose the HPP graph
segments:

```python
from hpp_exec import print_segments, segments_from_graph

configs, times, segments = segments_from_graph(p_timed, graph)
print_segments(segments)
```

Configure the actions from the states observed in the segment table:

```python
configure_execution_actions()
```

Conceptually, execution has three phases:

| # | Phase     | What the arm does           | Action before phase |
|---|-----------|-----------------------------|---------------------|
| 0 | approach  | move above the box, descend | start opening       |
| 1 | transport | carry the box to the goal   | wait, attach, close |
| 2 | retreat   | lift and return             | open and detach     |

`background_open_gripper.start()` returns immediately, so the arm can begin the
approach while the gripper controller opens the fingers. The later
`background_open_gripper.wait()` blocks before the grasp transition, and
`grasp_box()` runs after that segment so the fingers close once the arm has
reached the object.

## Executing the segments

Send the arm segments to the arm controller and let the segment actions command
the gripper controller:

```python
from hpp_exec import execute_segments

configure_execution_actions()
close_gripper()
reset_box_pose()
execute_segments(
    segments, configs, times,
    joint_names=[f"fr3_joint{i}" for i in range(1, 8)],
    joint_indices=list(range(7)),
)
```

`close_gripper()` is only a setup step to make the overlapping opening visible
in Gazebo. During execution you should see the fingers open while the arm
starts the approach, then the plan waits before grasping, closes on the box,
carries it to the goal, opens again, and retreats.

`reset_box_pose()` detaches the simulated box if needed and places it back at
the planned start pose before execution.
