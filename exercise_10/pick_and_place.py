# ruff: noqa: F401 -- Imports used when completing the exercise.
import numpy as np
from environment import initial_configuration, load_scene, set_environment_margins
from pinocchio import SE3
from pyhpp.core import ConfigProjector, Progressive
from pyhpp.core.path import Vector
from pyhpp.manipulation import (
    Device,
    EnforceTransitionSemantic,
    Graph,
    GraphPathValidation,
    GraphRandomShortcut,
    ManipulationPlanner,
    Problem,
    urdf,
)
from pyhpp.manipulation.constraint_graph_factory import ConstraintGraphFactory
from pyhpp_viser import Viewer
from tools import SplineToppra


def display():
    v = Viewer(robot)
    v.initViewer(open=False, loadModel=True)
    v.setProblem(problem)
    v.setGraph(graph)
    return v


robot = Device("mfja")

# Load Staubli robot in MFJA room 315 environment
load_scene(robot)

# Keep the arm facing the fixtures with the elbow in its initial posture.
robot.setJointBounds("staubli/joint_1", np.deg2rad([-90.0, 90.0]).tolist())
robot.setJointBounds("staubli/joint_3", [0.0, robot.model().upperPositionLimit[2]])

# Load 42 mm gear
urdf_filename = "package://mfja_3rd_floor_description/urdf/gear_42.urdf"
srdf_filename = "package://mfja_3rd_floor_description/srdf/gear_42.srdf"

urdf.loadModel(
    robot, 0, "gear_42", "freeflyer", urdf_filename, srdf_filename, SE3.Identity()
)

robot.setJointBounds(
    "gear_42/root_joint",
    [
        -1.0,
        1.0,
        -1.0,
        1.0,
        -0.2,
        1.5,
    ],
)

problem = Problem(robot)
problem.pathValidation(GraphPathValidation(Progressive(robot, 0.001)))
problem.pathValidationFactory(GraphPathValidation(Progressive(robot, 0.001)))

graph = Graph("robot", robot, problem)
factory = ConstraintGraphFactory(graph)
graph.maxIterations(40)
graph.errorThreshold(1e-5)

# TODO: Build the constraint graph using the factory as in tutorial_1


# Initialize the graph once constructed
graph.initialize()

q = initial_configuration(robot)

# Read initial configuration robot in global variable q_start if defined
q[:6] = globals().get("q_start", q[:6])

# Build a configuration where gear_42 is placed on gripper gear_placement/placement_1
g = robot.grippers()["gear_plate/placement_1"]
h = robot.handles()["gear_42/placement"]
grasp = h.createGrasp(g, "gear_plate/placement_1 grasps gear_42/placement")
cp = ConfigProjector(robot, "solver", 1e-5, 40)
cp.add(grasp, 0)
q1, status = cp.solver().solve(q)
assert status

# TODO: As just above, build a configuration q2 where gear_42 is placed on gripper
#       gear_placement/placement_2

# TODO: Define and solve a manipulation problem with
#         - initial configuration q1 and,
#         - final configuration q2.
#       Take inspiration from tutorial_5 for
#         - path optimization, and
#         - time parameterization.

# WARNING: In the model of the robot, the gripper rigid and closed. As a consequence, the
#          robot cannot grasp the object without collision.
# TODO:    Deactivate collisions between the gripper and the part along transitions containing
#          grasp configurations. For that, unlike in tutorial_3 use method
#          graph.setSecurityMarginForTransition(transition, j1, j2, float("-inf"))
#          where
#            - transition is the result of graph.getTransition(transition_name),
#            - j1 and j2 are joints names among those returned by method robot.getJoinNames().
#
