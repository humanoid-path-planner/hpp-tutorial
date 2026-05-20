import time

import numpy as np
import rclpy
from geometry_msgs.msg import Pose
from hpp_exec import (
    print_segments,
    segments_from_graph,
    send_trajectory,
)
from pinocchio import SE3
from pyhpp.constraints import ComparisonType, ComparisonTypes, LockedJoint
from pyhpp.core import RandomShortcut, SimpleTimeParameterization
from pyhpp.manipulation import (
    Device,
    EnforceTransitionSemantic,
    Graph,
    ManipulationPlanner,
    Problem,
    urdf,
)
from pyhpp.manipulation.constraint_graph_factory import ConstraintGraphFactory
from pyhpp_viser import Viewer
from rclpy.node import Node
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import SetEntityPose
from std_msgs.msg import Empty


def display():
    v = Viewer(robot)
    v.initViewer(open=False, loadModel=True)
    v.setProblem(problem)
    v.setGraph(graph)
    return v


ARM_JOINT_NAMES = [f"fr3_joint{i}" for i in range(1, 8)]
GRIPPER_JOINT_NAMES = ["fr3_finger_joint1"]
BOX_INITIAL_POSITION = (0.4, -0.2, 0.0251)
BOX_GOAL_POSITION = (0.4, 0.2, 0.0251)


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
        *BOX_INITIAL_POSITION,
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
        *BOX_GOAL_POSITION,
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

semantic = EnforceTransitionSemantic(problem)
p_opt = semantic.optimize(p_opt)

# Time-parameterize for execution
stp = SimpleTimeParameterization(problem)
stp.order = 2
stp.safety = 0.95
stp.maxAcceleration = 1.0
p_timed = stp.optimize(p_opt)
print(f"Trajectory duration: {p_timed.length():.3f} s")

print("Timed path ready for visualization and execution.")
print()
print("To visualize:")
print("  v = display()")
print("  v.loadPath(p_timed)")
print()

configs, times, segments = segments_from_graph(p_timed, graph)

if not rclpy.ok():
    rclpy.init()

gazebo_node = Node("tutorial_7_box_controller")
attach_pub = gazebo_node.create_publisher(Empty, "/box/attach", 1)
detach_pub = gazebo_node.create_publisher(Empty, "/box/detach", 1)
pose_client = gazebo_node.create_client(SetEntityPose, "/world/empty/set_pose")


def attach_box():
    attach_pub.publish(Empty())
    rclpy.spin_once(gazebo_node, timeout_sec=0.05)
    time.sleep(0.2)
    gazebo_node.get_logger().info("Published '/box/attach' on Gazebo topic")
    return True


def detach_box():
    detach_pub.publish(Empty())
    rclpy.spin_once(gazebo_node, timeout_sec=0.05)
    time.sleep(0.2)
    gazebo_node.get_logger().info("Published '/box/detach' on Gazebo topic")
    return True


def reset_box_pose(xyz=BOX_INITIAL_POSITION):
    if not detach_box():
        return False

    if not pose_client.wait_for_service(timeout_sec=3.0):
        gazebo_node.get_logger().error("Gazebo pose service is unavailable")
        return False

    req = SetEntityPose.Request()
    req.entity.name = "box"
    req.entity.type = Entity.MODEL
    req.pose = Pose()
    req.pose.position.x = float(xyz[0])
    req.pose.position.y = float(xyz[1])
    req.pose.position.z = float(xyz[2])
    req.pose.orientation.w = 1.0

    future = pose_client.call_async(req)
    rclpy.spin_until_future_complete(gazebo_node, future, timeout_sec=3.0)
    result = future.result()
    if result is None or not result.success:
        gazebo_node.get_logger().error("Failed to reset the Gazebo box pose")
        return False

    time.sleep(0.2)
    gazebo_node.get_logger().info(
        f"Reset box pose to x={xyz[0]:.3f}, y={xyz[1]:.3f}, z={xyz[2]:.3f}"
    )
    return True


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


def grasp_box():
    return attach_box() and close_gripper()


def release_box():
    return open_gripper() and detach_box()


print(f"Extracted {len(configs)} waypoints.")
print_segments(segments)

print("Useful helpers:")
print("  open_gripper()")
print("  close_gripper()")
print("  grasp_box()")
print("  release_box()")
print("  attach_box()")
print("  detach_box()")
print("  reset_box_pose()")
