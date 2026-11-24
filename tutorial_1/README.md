# Installing the software

The tutorials use the binary packages of HPP on Ubuntu 24.04. Tutorials 6 to 9 also use ROS 2 Jazzy. For other installation methods, please visit the [installation page](https://humanoid-path-planner.github.io/hpp-doc/installation/installation.html).

## Installing HPP

  1. Install HPP by following the [binary installation on Ubuntu 24.04](https://humanoid-path-planner.github.io/hpp-doc/installation/stable-binary.html), with its environment variables.
  2. Install the packages used by the tutorials:

```
sudo apt-get install robotpkg-py312-hpp-tutorial robotpkg-py312-hpp-toppra \
robotpkg-py312-qt5-hpp-plot python3-matplotlib python3-venv
```

  3. Install the web viewer in a virtual environment that keeps the system packages:

```
python3 -m venv --system-site-packages ~/hpp-venv
. ~/hpp-venv/bin/activate
pip install viser pycollada
```

  4. Get the tutorial scripts:

```
git clone --branch v10.0.0 https://github.com/humanoid-path-planner/hpp-tutorial hpp_tutorial
```

In each new terminal, activate the virtual environment:

```
. ~/hpp-venv/bin/activate
```

You can now proceed to [tutorial 2](../tutorial_2/README.md).

## Installing ROS 2 for tutorials 6 to 9

  1. Install ROS 2 Jazzy by following the [ROS 2 documentation](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html). Add `source /opt/ros/jazzy/setup.bash` to your `.bashrc`, before the environment variables of HPP.
  2. Install the ROS 2 packages used by the tutorials:

```
sudo apt-get install python3-colcon-common-extensions ros-jazzy-fastcdr \
ros-jazzy-control-msgs ros-jazzy-trajectory-msgs ros-jazzy-joint-state-broadcaster \
ros-jazzy-joint-trajectory-controller ros-jazzy-controller-manager ros-jazzy-ros2controlcli \
ros-jazzy-rviz2 ros-jazzy-rviz-common ros-jazzy-rviz-rendering ros-jazzy-pluginlib \
ros-jazzy-ament-cmake ros-jazzy-ament-lint-auto \
ros-jazzy-gz-sim-vendor ros-jazzy-gz-plugin-vendor ros-jazzy-sdformat-urdf \
ros-jazzy-gz-ros2-control ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge \
ros-jazzy-joint-state-publisher-gui ros-jazzy-xacro
```

  3. Build the RViz2 plugins of HPP, `hpp-exec` and the Franka robot in a workspace:

```
mkdir -p ~/hpp_ws/src
cd ~/hpp_ws/src
git clone --branch v10.0.0 https://github.com/humanoid-path-planner/hpp-rviz
git clone --branch v10.0.0 https://github.com/humanoid-path-planner/hpp-exec
git clone --branch 2.6.0 --depth 1 https://github.com/frankarobotics/franka_description
git clone --branch v3.2.2 --depth 1 https://github.com/frankarobotics/franka_ros2
cd ~/hpp_ws
colcon build --packages-select hpp_rviz hpp_exec franka_description franka_mobile_sensors \
franka_gazebo_bringup --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
```

In each new terminal, also source the workspace:

```
source ~/hpp_ws/install/local_setup.bash
```
