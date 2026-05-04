import numpy as np
import time
from pinocchio import SE3
from pyhpp.constraints import ComparisonType, ComparisonTypes, LockedJoint
from pyhpp.core import RandomShortcut, SimpleTimeParameterization
from pyhpp.manipulation import Device, Graph, ManipulationPlanner, Problem, urdf
from pyhpp.manipulation.constraint_graph_factory import ConstraintGraphFactory
from pyhpp_viser import Viewer

try:
    import rclpy
    from geometry_msgs.msg import Pose
    from rclpy.node import Node
    from ros_gz_interfaces.msg import Entity
    from ros_gz_interfaces.srv import SetEntityPose
    from std_msgs.msg import Empty

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


class _UnavailableGazeboExecution:
    def __init__(self, import_error):
        self._import_error = import_error

    def raise_unavailable(self):
        raise RuntimeError(
            "ROS2 / Gazebo execution helpers are unavailable in this Python "
            "environment."
        ) from self._import_error

    def attach(self):
        self.raise_unavailable()

    def detach(self):
        self.raise_unavailable()

    def reset_pose(self, *_args, **_kwargs):
        self.raise_unavailable()


if ROS_EXECUTION_AVAILABLE:

    class GazeboBoxController:
        def __init__(
            self,
            world_name="empty",
            attach_topic="/box/attach",
            detach_topic="/box/detach",
            pose_service=None,
            settle_time=0.2,
        ):
            self.attach_topic = attach_topic
            self.detach_topic = detach_topic
            self.pose_service = pose_service or f"/world/{world_name}/set_pose"
            self.settle_time = settle_time
            self._node = None
            self._attach_pub = None
            self._detach_pub = None
            self._pose_client = None
            self._attached = False

        def _ensure_node(self):
            if self._node is not None:
                return self._node

            if not rclpy.ok():
                rclpy.init()

            self._node = Node("tutorial_7_box_controller")
            self._attach_pub = self._node.create_publisher(Empty, self.attach_topic, 1)
            self._detach_pub = self._node.create_publisher(Empty, self.detach_topic, 1)
            self._pose_client = self._node.create_client(
                SetEntityPose, self.pose_service
            )
            return self._node

        def _publish(self, publisher_attr, action_name):
            node = self._ensure_node()
            publisher = getattr(self, publisher_attr)
            publisher.publish(Empty())
            rclpy.spin_once(node, timeout_sec=0.05)
            time.sleep(self.settle_time)
            node.get_logger().info(f"Published '{action_name}' on Gazebo topic")
            return True

        def attach(self):
            if self._attached:
                return True
            ok = self._publish("_attach_pub", self.attach_topic)
            if ok:
                self._attached = True
            return ok

        def detach(self):
            ok = self._publish("_detach_pub", self.detach_topic)
            if ok:
                self._attached = False
            return ok

        def reset_pose(self, xyz=BOX_INITIAL_POSITION):
            node = self._ensure_node()

            if not self.detach():
                return False

            if not self._pose_client.wait_for_service(timeout_sec=3.0):
                node.get_logger().error(
                    f"Gazebo pose service '{self.pose_service}' is unavailable"
                )
                return False

            req = SetEntityPose.Request()
            req.entity.name = "box"
            req.entity.type = Entity.MODEL
            req.pose = Pose()
            req.pose.position.x = float(xyz[0])
            req.pose.position.y = float(xyz[1])
            req.pose.position.z = float(xyz[2])
            req.pose.orientation.w = 1.0

            future = self._pose_client.call_async(req)
            rclpy.spin_until_future_complete(node, future, timeout_sec=3.0)
            result = future.result()
            if result is None or not result.success:
                node.get_logger().error("Failed to reset the Gazebo box pose")
                return False

            time.sleep(self.settle_time)
            node.get_logger().info(
                f"Reset box pose to x={xyz[0]:.3f}, y={xyz[1]:.3f}, z={xyz[2]:.3f}"
            )
            return True

    box_controller = GazeboBoxController()

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
        return box_controller.attach() and close_gripper()

    def release_box():
        return open_gripper() and box_controller.detach()

    def prepare_sim_for_run():
        return box_controller.reset_pose(BOX_INITIAL_POSITION) and open_gripper()

    segments = segments_from_graph(
        configs,
        times,
        graph,
        on_grasp=grasp_box,
        on_release=release_box,
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
    print("  prepare_sim_for_run()")
    print("  execute_on_gazebo()")
    print()
    print("Useful helpers:")
    print("  open_gripper()")
    print("  close_gripper()")
    print("  box_controller.attach()")
    print("  box_controller.detach()")
    print("  box_controller.reset_pose()")
else:
    box_controller = _UnavailableGazeboExecution(ROS_EXECUTION_IMPORT_ERROR)
    segments = None

    def _unavailable(*_args, **_kwargs):
        box_controller.raise_unavailable()

    open_gripper = _unavailable
    close_gripper = _unavailable
    grasp_box = _unavailable
    release_box = _unavailable
    prepare_sim_for_run = _unavailable
    execute_on_gazebo = _unavailable

    print("ROS2 / Gazebo execution helpers are unavailable in this Python env.")
    print(f"Import error: {ROS_EXECUTION_IMPORT_ERROR}")
