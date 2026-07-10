"""Launch Franka FR3 with gripper in Gazebo for HPP tutorial 8 (pick and place).

Usage (inside the docker container):
    ros2 launch /home/user/devel/install/share/hpp_tutorial/tutorial_8/launch_sim.py
"""

import os

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchContext, LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def get_robot_description_and_controllers(context: LaunchContext, robot_type):
    robot_type_str = context.perform_substitution(robot_type)

    tutorial_dir = os.path.join(
        get_package_share_directory("hpp_tutorial"), "tutorial_8"
    )
    controllers_yaml = os.path.join(tutorial_dir, "controllers.yaml")

    franka_xacro = os.path.join(
        get_package_share_directory("franka_gazebo_bringup"),
        "urdf",
        "franka_arm.gazebo.xacro",
    )

    robot_description_xml = xacro.process_file(
        franka_xacro,
        mappings={
            "robot_type": robot_type_str,
            "hand": "true",
            "ros2_control": "true",
            "gazebo": "true",
            "ee_id": "franka_hand",
        },
    ).toxml()

    detachable_joint_plugin = f"""
  <gazebo>
    <plugin filename="gz-sim-detachable-joint-system" name="gz::sim::systems::DetachableJoint">
      <parent_link>{robot_type_str}_hand</parent_link>
      <child_model>box</child_model>
      <child_link>base_link</child_link>
      <attach_topic>/box/attach</attach_topic>
      <detach_topic>/box/detach</detach_topic>
      <suppress_child_warning>true</suppress_child_warning>
    </plugin>
  </gazebo>
</robot>
"""
    robot_description_xml = robot_description_xml.replace(
        "</robot>", detachable_joint_plugin
    )

    # Replace the Franka default controllers YAML with our tutorial controllers
    franka_controllers = os.path.join(
        get_package_share_directory("franka_gazebo_bringup"),
        "config",
        "franka_gazebo_controllers.yaml",
    )
    robot_description_xml = robot_description_xml.replace(
        franka_controllers, controllers_yaml
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[{"robot_description": robot_description_xml}],
    )

    spawn_jsb = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    spawn_jtc = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller"],
        output="screen",
    )

    spawn_gripper = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller"],
        output="screen",
    )

    return [robot_state_publisher, spawn_jsb, spawn_jtc, spawn_gripper]


def generate_launch_description():
    robot_type = LaunchConfiguration("robot_type")
    tutorial_share = get_package_share_directory("hpp_tutorial")
    box_urdf = os.path.join(tutorial_share, "urdf", "box.urdf")
    ground_urdf = os.path.join(tutorial_share, "urdf", "ground.urdf")

    # Gazebo Sim
    os.environ["GZ_SIM_RESOURCE_PATH"] = os.path.dirname(
        get_package_share_directory("franka_description")
    )
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("ros_gz_sim"),
                "launch",
                "gz_sim.launch.py",
            )
        ),
        launch_arguments={"gz_args": "empty.sdf -r"}.items(),
    )

    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "/robot_description"],
        output="screen",
    )

    spawn_box = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name",
            "box",
            "-file",
            box_urdf,
            "-x",
            "0.4",
            "-y",
            "-0.2",
            "-z",
            "0.0251",
        ],
        output="screen",
    )

    spawn_ground = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name",
            "ground",
            "-file",
            ground_urdf,
            "-x",
            "0.0",
            "-y",
            "0.0",
            "-z",
            "0.0",
        ],
        output="screen",
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/box/attach@std_msgs/msg/Empty]gz.msgs.Empty",
            "/box/detach@std_msgs/msg/Empty]gz.msgs.Empty",
            "/world/empty/set_pose@ros_gz_interfaces/srv/SetEntityPose",
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("robot_type", default_value="fr3"),
            gazebo,
            OpaqueFunction(
                function=get_robot_description_and_controllers, args=[robot_type]
            ),
            spawn,
            spawn_ground,
            spawn_box,
            bridge,
        ]
    )
