"""Stäubli gripper IO and measured joint-position checks."""

import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np

SLOW_RATIO = 0.005

JOINT_NAMES = [f"joint_{i}" for i in range(1, 7)]


def set_gripper(node, config, mode):
    import rclpy
    from staubli_msgs.msg import IOModule, ServiceReturnCode
    from staubli_msgs.srv import WriteSingleIO

    client = node.create_client(WriteSingleIO, config["gripper_service"])
    try:
        if not client.wait_for_service(timeout_sec=5.0):
            raise RuntimeError("Gripper service unavailable")
        request = WriteSingleIO.Request()
        request.module.id = IOModule.VALVE_OUT
        request.pin = config["gripper_pin"]
        request.state = mode == "open"
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node, future, timeout_sec=5.0)
        response = future.result()
        if response is None or response.code.val != ServiceReturnCode.SUCCESS:
            raise RuntimeError("Gripper command failed")
        time.sleep(config["gripper_settle_s"])
    finally:
        node.destroy_client(client)
    return True


def check_position(node, config, target):
    current = read_joints(node, config)
    error = float(np.max(np.abs(current - target)))
    if error > config["joint_tolerance_rad"]:
        raise RuntimeError(f"Le robot a changé de position ({error:.4f} rad)")
    return current


def lock_hardware():
    import fcntl
    import os
    import tempfile

    lock = (Path(tempfile.gettempdir()) / f"gear-calibration-{os.getuid()}.lock").open(
        "a"
    )
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        raise RuntimeError(
            "Un pointage ou une exécution est déjà ouvert, éventuellement suspendu. "
            "Le fermer avec Ctrl+C."
        ) from None
    return lock


@contextmanager
def robot_connection():
    """Open a ROS session shared by gear execution and calibration."""
    import rclpy
    from rclpy.node import Node
    from rclpy.signals import SignalHandlerOptions

    with lock_hardware():
        # Python handles Ctrl+C while ROS stays available for cancellation.
        rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
        try:
            node = Node("gear_execution")
            try:
                yield node
            finally:
                node.destroy_node()
        finally:
            rclpy.try_shutdown()


def read_status(node):
    from industrial_msgs.msg import RobotStatus
    from rclpy.wait_for_message import wait_for_message

    received, status = wait_for_message(
        RobotStatus, node, "/robot_status", time_to_wait=5
    )
    if not received:
        raise RuntimeError("Statut du contrôleur indisponible sur /robot_status")
    return status


def check_status(node):
    from industrial_msgs.msg import TriState

    status = read_status(node)
    # RobotStatus uses motion_possible for permission; in_error may coexist.
    if (
        status.motion_possible.val != TriState.TRUE
        or status.error_code != 0
        or status.e_stopped.val != TriState.FALSE
        or status.drives_powered.val != TriState.TRUE
        or status.in_motion.val != TriState.FALSE
    ):
        raise RuntimeError(f"Contrôleur non prêt (code {status.error_code})")


def check_speed(node):
    import rclpy
    from rcl_interfaces.srv import GetParameters

    client = node.create_client(
        GetParameters, "/joint_trajectory_interface/get_parameters"
    )
    try:
        if not client.wait_for_service(timeout_sec=5):
            raise RuntimeError("Paramètres du pilote indisponibles")
        request = GetParameters.Request(names=["default_velocity_ratio"])
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node, future, timeout_sec=5)
        response = future.result()
        if response is None or len(response.values) != 1:
            raise RuntimeError("Vitesse du pilote inconnue")
        ratio = response.values[0].double_value
        if not 0 < ratio <= SLOW_RATIO:
            raise RuntimeError(
                "Relancer le pilote avec le YAML produit par --write-driver-config"
            )
    finally:
        node.destroy_client(client)


def read_joints(node, config):
    from hpp_exec import read_current_configuration

    q = read_current_configuration(
        node,
        JOINT_NAMES,
        topic=config["joint_state_topic"],
        require_single_publisher=True,
    )
    if q is None or not np.isfinite(q).all():
        raise RuntimeError("Position mesurée du robot indisponible")
    return q


def wait_reached(node, config, result, configs):
    """Confirm the target with fresh measurements and a stopped controller."""
    from action_msgs.msg import GoalStatus
    from control_msgs.action import FollowJointTrajectory
    from industrial_msgs.msg import TriState

    started = last_progress = time.monotonic()
    previous = configs[0]
    arrived_since = None
    trajectory_started = False
    while time.monotonic() - started < 300:
        q = read_joints(node, config)
        status = read_status(node)
        now = time.monotonic()
        error = float(np.max(np.abs(q - configs[-1])))
        trajectory_started = trajectory_started or (
            status.trajectory_complete.val == TriState.FALSE
            or np.max(np.abs(q - configs[0])) > config["joint_tolerance_rad"]
            or result.done()
        )
        if result.done():
            reply = result.result()
            if (
                reply.status != GoalStatus.STATUS_SUCCEEDED
                or reply.result.error_code != FollowJointTrajectory.Result.SUCCESSFUL
            ):
                raise RuntimeError(
                    f"Mouvement non confirmé : statut ROS={reply.status}"
                )
        if (
            status.e_stopped.val != TriState.FALSE
            or status.error_code != 0
            or status.motion_possible.val != TriState.TRUE
        ):
            raise RuntimeError(
                f"Mouvement interrompu par le contrôleur (code {status.error_code})"
            )
        if np.max(np.abs(q - previous)) > 1e-5:
            previous = q
            last_progress = now
        if (
            trajectory_started
            and error <= config["joint_tolerance_rad"]
            and status.in_motion.val == TriState.FALSE
        ):
            if status.trajectory_complete.val == TriState.TRUE:
                return q
            if arrived_since is None:
                arrived_since = now
        else:
            arrived_since = None
        if now - last_progress > 10 and arrived_since is None:
            raise RuntimeError(
                f"Robot immobile hors cible depuis 10 s (écart {np.rad2deg(error):.4f}°)"
            )
        if arrived_since is not None and now - arrived_since > 5:
            raise RuntimeError(
                "Cible atteinte, mais VAL3 ne confirme pas la fin depuis 5 s"
            )
    raise RuntimeError("Mouvement non confirmé après 300 s")
