import numpy as np
from pinocchio import SE3, neutral
from pyhpp.manipulation import (
    Device,
    Graph,
    Problem,
    TransitionPlanner,
    urdf,
)
from pyhpp.manipulation.constraint_graph_factory import ConstraintGraphFactory
from pyhpp.manipulation.security_margins import SecurityMargins
from pyhpp_viser import Viewer


def display():
    v = Viewer(robot)
    v.initViewer(open=False, loadModel=True)
    v.setProblem(problem)
    v.setGraph(graph)
    return v


# use v = display() to create a Viewer instance.

robot = Device("tuto")

urdf_filename = "package://hpp_tutorial/urdf/staubli-drill.urdf"
srdf_filename = "package://hpp_tutorial/srdf/staubli-drill.srdf"

urdf.loadModel(
    robot, 0, "staubli", "anchor", urdf_filename, srdf_filename, SE3.Identity()
)

urdf_filename = "package://hpp_tutorial/urdf/square-plate.urdf"
srdf_filename = ""

urdf.loadModel(
    robot, 0, "plate", "freeflyer", urdf_filename, srdf_filename, SE3.Identity()
)
robot.setJointBounds(
    "plate/root_joint",
    [
        0,
        2,
        -1,
        1,
        0,
        2,
        -float("Inf"),
        float("Inf"),
        -float("Inf"),
        float("Inf"),
        -float("Inf"),
        float("Inf"),
        -float("Inf"),
        float("Inf"),
    ],
)

# Load an obstacle between robot and plate to force a non-straight path
obstacle_pose = SE3(rotation=np.identity(3), translation=np.array([0.5, -0.2, 1.2]))
urdf.loadModel(
    robot,
    0,
    "obstacle",
    "anchor",
    "package://hpp_tutorial/urdf/obstacle.urdf",
    "",
    obstacle_pose,
)

# Position the plate in the environment
q_init = neutral(robot.model())
r = robot.rankInConfiguration["plate/root_joint"]
q_init[r : r + 3] = [0.8, 0, 1]

# Add a handle on the plate
R = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])
T = np.array([0.02, 0, 0])
pose = SE3(rotation=R, translation=T)
robot.addHandle("plate/base_link", "plate/hole", pose, 0.1, 6 * [True])
handle = robot.handles()["plate/hole"]
handle.approachingDirection = np.array([0, 0, 1])

# Build the constraint graph
problem = Problem(robot)
graph = Graph("robot", robot, problem)
factory = ConstraintGraphFactory(graph)
factory.setGrippers(["staubli/tooltip"])
objects = ["plate"]
handlesPerObject = [["plate/hole"]]
contactsPerObject = [[]]
factory.setObjects(objects, handlesPerObject, contactsPerObject)
factory.generate()
# Set security margins
sm = SecurityMargins(problem, factory, ["staubli", "plate"], robot)
sm.setSecurityMarginBetween("staubli", "plate", 0.05)
sm.apply()
# Deactivate collision checking between robot last joint and plate for the last part of the
# motion
transition = graph.getTransition("staubli/tooltip > plate/hole | f_12")
graph.setSecurityMarginForTransition(
    transition, "staubli/joint_6", "plate/root_joint", float("-inf")
)
graph.initialize()
problem.constraintGraph(graph)

shooter = problem.configurationShooter()

# Plan motions between waypoint configurations
planner = TransitionPlanner(problem)
planner.maxIterations(1000)
p1 = None
for i in range(50):
    # Project random configuration on pregrasp waypoint state
    transition = graph.getTransition("staubli/tooltip > plate/hole | f_01")
    q = shooter.shoot()
    res, qpg, err = graph.generateTargetConfig(transition, q_init, q)
    if not res:
        continue
    # Check the configuration for collision
    pv = transition.pathValidation()
    res, report = pv.validateConfiguration(qpg)
    if not res:
        continue
    # plan motion between q_init and qpg
    planner.setTransition(transition)
    try:
        q_goal = np.zeros((robot.configSize(), 1))
        q_goal[:,0] = qpg
        p1 = planner.computePath(q_init, q_goal, True)
    except Exception as exc:
        print(f"path planning failed between q_init and qpg: {exc}")
        continue
    break

if p1 is None:
    print("Failed to plan p1 after 50 attempts. Try running the script again.")
else:
    print(f"Path p1 planned (q_init -> qpg), length: {p1.length():.3f}")
