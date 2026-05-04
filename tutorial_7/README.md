# Pick and place with gripper

## Prerequisite

Having completed [tutorial 6](../tutorial_6/README.md).

## Overview

Tutorial 6 executed a single arm trajectory. Pick-and-place adds a second
actuator - the gripper - whose state must change in the middle of the path:
open on approach, closed during transport, open again after release.

This tutorial builds an HPP manipulation constraint graph, solves a
pick-and-place problem, then executes it in Gazebo with the arm trajectory,
gripper motion, and box attachment coordinated automatically.

## Setting up the simulation

Use the same Docker image as tutorial 6 (`hpp-ros2:tuto`). If you have not
built it yet, see the [tutorial 6 instructions](../tutorial_6/README.md).

## Terminal 1: Launching the simulation

Launch Gazebo with the FR3 including its gripper:

```
ros2 launch hpp_tutorial tutorial_7_launch.py
```

Wait until you see `Configured and activated gripper_controller` in the output.
The launch file also spawns the ground plane and the box, then bridges the
Gazebo topics used to attach/detach the box.

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
`times`, describing the full planned motion, including the waypoints where a
grasp is acquired or released.

You can visualize the path in the browser viewer:

```python
v = display()
v.loadPath(p_timed)
```

## Executing

Before each run, reset the simulated box and open the gripper:

```python
prepare_sim_for_run()
```

Then execute the planned motion:

```python
execute_on_gazebo()
```

Expected behaviour in Gazebo: the gripper opens, descends onto the box, the
box is attached to the hand, the fingers close, the arm carries it to the goal,
the fingers open, the box is detached, and the arm retreats.

## Understanding the execution

The script builds the execution segments for you. For this problem there are
three phases:

1. approach the box with the gripper open,
2. grasp the box and transport it,
3. release the box and retreat.

The details of how `hpp-exec` detects grasp/release transitions from the HPP
constraint graph, builds segments, and calls gripper actions are documented in
the [hpp-exec documentation](https://gepetto.github.io/doc/hpp-exec/doxygen-html/index.html#hpp_exec_grasps).

## Experiment

Run the same planned path twice:

```python
prepare_sim_for_run()
execute_on_gazebo()
prepare_sim_for_run()
execute_on_gazebo()
```

The second `prepare_sim_for_run()` call should put the box back at the initial
pose before replaying the motion.
