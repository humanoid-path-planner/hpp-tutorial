# Extends the base tutorial image with ROS2 control + Gazebo + Franka packages
# for executing planned trajectories on a simulated Panda/FR3 robot.
#
# Build:  docker build --build-arg DOCKER_USER=`id -u` --build-arg DOCKER_GROUP=`id -g` -t hpp-ros2:tuto .
# Run:    See tutorial_6/README.md for docker run instructions.

FROM hpp:tuto

ARG FRANKA_DESCRIPTION_VERSION=2.6.0
ARG FRANKA_ROS2_VERSION=v3.2.2

USER root

# ROS2 control packages
RUN apt-get update -y && DEBIAN_FRONTEND=noninteractive apt-get install -qqy \
    ros-jazzy-control-msgs \
    ros-jazzy-trajectory-msgs \
    ros-jazzy-joint-trajectory-controller \
    ros-jazzy-controller-manager \
    ros-jazzy-ros2controlcli \
    python3-colcon-common-extensions

# Gazebo Harmonic + ROS2 bridge
RUN apt-get update -y && DEBIAN_FRONTEND=noninteractive apt-get install -qqy \
    ros-jazzy-gz-sim-vendor \
    ros-jazzy-gz-plugin-vendor \
    ros-jazzy-sdformat-urdf \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-xacro \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Franka packages used by the tutorial. Pin the source versions because the
# upstream jazzy branch can add runtime dependencies for hardware controllers
# that are not needed for this Gazebo-only example.
WORKDIR /opt/franka_ws
RUN mkdir -p src \
    && cd src \
    && git clone --branch ${FRANKA_DESCRIPTION_VERSION} --depth 1 https://github.com/frankarobotics/franka_description.git \
    && git clone --branch ${FRANKA_ROS2_VERSION} --depth 1 https://github.com/frankarobotics/franka_ros2.git

RUN chown -R user:user /opt/franka_ws

USER user

RUN . /opt/ros/jazzy/setup.sh \
    && colcon build --packages-select \
        franka_description \
        franka_mobile_sensors \
        franka_gazebo_bringup \
    --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF

RUN echo 'source /opt/franka_ws/install/setup.bash 2>/dev/null' >> /home/user/.bashrc

WORKDIR /home/user/devel
