import numpy as np
from pinocchio import SE3
from pyhpp.constraints import ComparisonType, ComparisonTypes, LockedJoint
from pyhpp.core import RandomShortcut, SimpleTimeParameterization
from pyhpp.manipulation import Device, Graph, ManipulationPlanner, Problem, urdf
from pyhpp.manipulation.constraint_graph_factory import ConstraintGraphFactory
from pyhpp_viser import Viewer

try:
    from hpp_exec import execute_segments, segments_from_graph, send_trajectory

    ROS_EXECUTION_AVAILABLE = True
    ROS_EXECUTION_IMPORT_ERROR = None
except ImportError as exc:
    ROS_EXECUTION_AVAILABLE = False
    ROS_EXECUTION_IMPORT_ERROR = exc


def display():
    v = Viewer(robot)
    v.initViewer(open=False, loadModel=True)
    v.setProblem(problem)
    v.setGraph(graph)
    return v


ARM_JOINT_NAMES = [f"fr3_joint{i}" for i in range(1, 8)]
GRIPPER_JOINT_NAMES = ["fr3_finger_joint1"]


# Load FR3 robot with gripper
robot = Device("tuto")

urdf_filename = "package://hpp_tutorial/urdf/fr3.urdf"
srdf_filename = "package://hpp_tutorial/srdf/fr3.srdf"
urdf.loadModel(robot, 0, "fr3", "anchor", urdf_filename, srdf_filename, SE3.Identity())

# Load ground (fixed obstacle with contact surface)
urdf_filename = "package://hpp_tutorial/urdf/ground.urdf"
srdf_filename = "package://hpp_tutorial/srdf/ground.srdf"
urdf.loadModel(
    robot, 0, "ground", "anchor", urdf_filename, srdf_filename, SE3.Identity()
)

# Load box (freeflyer object with handle + contact surface)
urdf_filename = "package://hpp_tutorial/urdf/box.urdf"
srdf_filename = "package://hpp_tutorial/srdf/box.srdf"
urdf.loadModel(
    robot, 0, "box", "freeflyer", urdf_filename, srdf_filename, SE3.Identity()
)

# Set bounds for the box translation (needed for random sampling)
robot.setJointBounds(
    "box/root_joint",
    [
        -1.5,
        1.5,  # x
        -1.5,
        1.5,  # y
        -0.2,
        1.5,  # z
        -float("Inf"),
        float("Inf"),  # quaternion
        -float("Inf"),
        float("Inf"),
        -float("Inf"),
        float("Inf"),
        -float("Inf"),
        float("Inf"),
    ],
)

# Configuration vector:
#   indices 0-6:   fr3 arm joints (7 DOF)
#   indices 7-8:   fr3 finger joints (2 DOF)
#   indices 9-15:  box pose (x, y, z, qx, qy, qz, qw)

# Build constraint graph for manipulation
problem = Problem(robot)
graph = Graph("robot", robot, problem)
factory = ConstraintGraphFactory(graph)

graph.maxIterations(40)
graph.errorThreshold(1e-5)

factory.setGrippers(["fr3/gripper"])
factory.setObjects(["box"], [["box/handle"]], [["box/surface"]])
factory.environmentContacts(["ground/surface"])
factory.generate()

# Lock finger joints open during planning
cts = ComparisonTypes()
cts[:] = [ComparisonType.EqualToZero]
locked_fingers = []
for i in range(2):
    lj = LockedJoint(robot, f"fr3/fr3_finger_joint{i + 1}", np.array([0.035]), cts)
    locked_fingers.append(lj)

graph.addNumericalConstraintsToGraph(locked_fingers)
graph.initialize()

# Initial config: ready pose, open gripper, box in front at (0.4, -0.2)
q_init = np.array(
    [
        0,
        -0.785,
        0,
        -2.356,
        0,
        1.571,
        0.785,  # arm (ready)
        0.035,
        0.035,  # fingers (open)
        0.4,
        -0.2,
        0.0251,
        0,
        0,
        0,
        1,  # box pose (x,y,z, qx,qy,qz,qw)
    ]
)

# Goal config: same arm pose, box moved to (0.4, 0.2)
q_goal = np.array(
    [
        0,
        -0.785,
        0,
        -2.356,
        0,
        1.571,
        0.785,
        0.035,
        0.035,
        0.4,
        0.2,
        0.0251,
        0,
        0,
        0,
        1,
    ]
)

# Solve the manipulation problem
problem.initConfig(q_init)
problem.addGoalConfig(q_goal)
problem.constraintGraph(graph)

planner = ManipulationPlanner(problem)
planner.maxIterations(500)

print("Solving manipulation problem...")
try:
    p = planner.solve()
except Exception as exc:
    raise RuntimeError(
        "ManipulationPlanner failed to find a path. Try running the script "
        "again (randomized planner) or increase maxIterations."
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

# Extract waypoints
n_samples = 200
configs = []
times = []
for i in range(n_samples + 1):
    t = (i / n_samples) * p_timed.length()
    q, success = p_timed(t)
    if success:
        configs.append(np.array(q))
        times.append(t)

print(f"Extracted {len(configs)} waypoints, ready to execute.")
print()
print("To visualize:")
print("  v = display()")
print("  v.loadPath(p_timed)")
print()


if ROS_EXECUTION_AVAILABLE:

    def open_gripper():
        return send_trajectory(
            [np.array([0.0]), np.array([0.035])],
            [0.0, 0.5],
            joint_names=GRIPPER_JOINT_NAMES,
            controller_topic="/gripper_controller/follow_joint_trajectory",
        )

    def close_gripper():
        return send_trajectory(
            [np.array([0.035]), np.array([0.0])],
            [0.0, 0.5],
            joint_names=GRIPPER_JOINT_NAMES,
            controller_topic="/gripper_controller/follow_joint_trajectory",
        )

    segments = segments_from_graph(
        configs,
        times,
        graph,
        on_grasp=close_gripper,
        on_release=open_gripper,
    )
    if segments:
        segments[0].pre_actions.insert(0, open_gripper)

    def execute_on_gazebo():
        return execute_segments(
            segments,
            configs,
            times,
            joint_names=ARM_JOINT_NAMES,
            joint_indices=list(range(7)),
        )

    print("To execute on Gazebo:")
    print("  execute_on_gazebo()")
    print()
    print("Useful helpers:")
    print("  open_gripper()")
    print("  close_gripper()")
else:
    segments = None

    def _unavailable(*_args, **_kwargs):
        raise RuntimeError(
            "ROS2 execution helpers are unavailable in this Python environment."
        ) from ROS_EXECUTION_IMPORT_ERROR

    open_gripper = _unavailable
    close_gripper = _unavailable
    execute_on_gazebo = _unavailable

    print("ROS2 execution helpers are unavailable in this Python env.")
    print(f"Import error: {ROS_EXECUTION_IMPORT_ERROR}")
