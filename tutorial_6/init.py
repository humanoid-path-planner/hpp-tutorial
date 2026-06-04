import time

import numpy as np
import rclpy
from pinocchio import SE3
from pyhpp.core import BiRRTPlanner, Problem, RandomShortcut, SimpleTimeParameterization
from pyhpp.pinocchio import Device, urdf
from pyhpp_viser import Viewer
from rclpy.node import Node
from sensor_msgs.msg import JointState

ARM_JOINT_NAMES = [f"fr3_joint{i}" for i in range(1, 8)]
FINGER_OPEN = [0.035, 0.035]


def read_initial_configuration(timeout_sec=5.0):
    if not rclpy.ok():
        rclpy.init()

    node = Node("tutorial_6_initial_configuration")
    joint_states = []
    node.create_subscription(JointState, "/joint_states", joint_states.append, 1)
    deadline = time.monotonic() + timeout_sec
    try:
        while not joint_states and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)

        if not joint_states:
            raise RuntimeError("No message received on /joint_states.")

        joint_state = joint_states[-1]
        positions = dict(zip(joint_state.name, joint_state.position))
        missing = [name for name in ARM_JOINT_NAMES if name not in positions]
        if missing:
            raise RuntimeError(f"Missing joints in /joint_states: {missing}")

        return np.array([*(positions[name] for name in ARM_JOINT_NAMES), *FINGER_OPEN])
    finally:
        node.destroy_node()


def display():
    v = Viewer(robot)
    v.initViewer(open=False, loadModel=True)
    v.setProblem(problem)
    return v


# use v = display() to create a Viewer instance.

robot = Device("tuto")

# Load the Franka FR3 robot
urdf_filename = "package://hpp_tutorial/urdf/fr3.urdf"
srdf_filename = "package://hpp_tutorial/srdf/fr3.srdf"
urdf.loadModel(robot, 0, "fr3", "anchor", urdf_filename, srdf_filename, SE3.Identity())

# Configuration: 7 arm joints + 2 finger joints = 9 DOF
# Fingers are kept open (0.035 m)
q_init = read_initial_configuration()

# Goal: a different arm configuration
q_goal = np.array([1.0, -1.2, 0.5, -2.0, -0.5, 2.0, 0.3, 0.035, 0.035])

# Plan a path
problem = Problem(robot)
problem.initConfig(q_init)
problem.addGoalConfig(q_goal)

planner = BiRRTPlanner(problem)
planner.maxIterations(2000)

print("Solving...")
try:
    p = planner.solve()
except Exception as exc:
    raise RuntimeError(
        "BiRRT failed to find a path. Try running the script again "
        "(randomized planner) or increase maxIterations."
    ) from exc
print(f"Path found, length: {p.length():.3f}")

# Optimize
optimizer = RandomShortcut(problem)
p_opt = optimizer.optimize(p)
print(f"Optimized path length: {p_opt.length():.3f}")

# Time-parameterize for execution
stp = SimpleTimeParameterization(problem)
stp.order = 2
stp.safety = 0.95
stp.maxAcceleration = 1.0
p_timed = stp.optimize(p_opt)
print(f"Trajectory duration: {p_timed.length():.3f} s")
print()
print("Path ready. Follow the README to extract waypoints and send to Gazebo.")
