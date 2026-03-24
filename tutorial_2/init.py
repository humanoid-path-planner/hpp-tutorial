from pinocchio import SE3, neutral
from pyhpp.manipulation import Device, urdf

robot = Device("tuto")

urdf_filename = "package://example-robot-data/robots/panda_description/urdf/panda.urdf"
srdf_filename = "package://hpp_tutorial/srdf/panda.srdf"

urdf.loadModel(
    robot, 0, "panda", "anchor", urdf_filename, srdf_filename, SE3.Identity()
)

# Get neutral configuration of robot
q = neutral(robot.model())
# Open the gripper
q[-2:] = [0.035, 0.035]
