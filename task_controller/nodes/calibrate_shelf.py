#!/usr/bin/python

import roslib; roslib.load_manifest('task_controller')
import rospy
import subprocess
import moveit_commander
import yaml
import os

from geometry_msgs.msg import Pose, Point, Quaternion

depth = 0.87  # Depth of shelf
palm_offset = 0.165  # Offset from tool to palm

# Currently shelf + orientation are not calibrated
z = -0.045
orientation = {
    "x": 0.5,
    "y": 0.5,
    "z": 0.5,
    "w": 0.5,
}

default_orientation = Quaternion(
    x=0.557211015648,
    y=-0.438833281977,
    z=-0.561100598534,
    w=0.426740381256,
)

pose_left = Pose(
    position=Point(
        x=0.539323677836,
        y=0.433382331813,
        z=1.6160210999,
    ),
    orientation=default_orientation,
)

pose_right = Pose(
    position=Point(
        x=0.526801535149,
        y=-0.379182889409,
        z=0.88944822383,
    ),
    orientation=default_orientation,
)


if __name__ == '__main__':
    path = subprocess.check_output("rospack find task_controller", shell=True)
    path = path.strip("\n")
    rospy.init_node("motoman_apc_controller")

    robot = moveit_commander.RobotCommander()

    print "Starting up"
    skip = raw_input("Hit enter to move to initial pose or type skip to skip: ")
    if "s" not in skip:
        print "Left: ", robot.arm_left.go(pose_left)
        print "Right: ", robot.arm_right.go(pose_right)
    print "Please jog until the palms touch the shelf"
    raw_input("Hit enter to continue ")
    left = robot.arm_left.get_current_pose().pose
    right = robot.arm_right.get_current_pose().pose
    x = depth/2 + palm_offset + (left.position.x + right.position.x)/2
    y = (left.position.y + right.position.y)/2
    print "X =", x
    print "Y =", y

    cfg = {
        "shelf": {
            "position": {
                "x": x,
                "y": y,
                "z": z
            },
            "orientation": orientation
        }
    }

    filename = os.path.join(os.path.dirname(__file__), "../cfg/shelf.yaml")
    with open(filename, "w") as file:
        yaml.dump(cfg, file, default_flow_style=False)
