import numpy as np
from pinocchio import SE3
from pyhpp.pinocchio import Device, urdf
from pyhpp.core import Problem, BiRRTPlanner, RandomShortcut, SimpleTimeParameterization
from pyhpp_viser import Viewer


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

# Start: "ready" position (matches Gazebo initial pose)
q_init = np.array([0, -0.785, 0, -2.356, 0, 1.571, 0.785, 0.035, 0.035])

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
