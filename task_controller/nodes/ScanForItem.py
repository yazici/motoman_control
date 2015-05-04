import roslib; roslib.load_manifest('task_controller')
import rospy
import smach
import numpy
from math import cos, sin, pi
from tf import TransformListener
from transformation_helpers import PoseToMatrix, PoseFromMatrix

from apc_vision.srv import *
from apc_vision.msg import *


class SCANFORITEM(smach.State):

    def __init__(self, robot):
        smach.State.__init__(self, outcomes=['Success', 'Failure', 'Fatal'],
                             input_keys=['bin', 'item'],
                             output_keys=['pose', 'points'])
        self.arm = robot.arm_left_torso
        self.sample = rospy.ServiceProxy("sample_vision", SampleVision)
        self.process = rospy.ServiceProxy("process_vision", ProcessVision)
        self.tf = TransformListener(True, rospy.Duration(10.0))
        rospy.sleep(rospy.Duration(1.0))  # Wait for network timting

    def execute(self, userdata):
        rospy.loginfo("Trying to find "+userdata.item+"...")

        poses = self.get_poses()
        for i in range(5):
            try:
                self.sample_bin(userdata.bin, poses)
                response = self.process(
                    bin=userdata.bin,
                    target=APCObject(name=userdata.item, number=1),
                    objects=[],
                )
                userdata.pose = self.tf.transformPose("/base_link", response.pose)
                userdata.points = response.object_points
                print "Pose:", self.tf.transformPose("/base_link", response.pose)
                return 'Success'
            except rospy.ServiceException as e:
                rospy.logwarn("Error process: "+str(e))
        rospy.logwarn("Can't find "+userdata.item+"...")
        return 'Failure'

    def get_poses(self):
        center_pose = self.arm.get_current_pose().pose
        center_matrix = PoseToMatrix(center_pose)
        angle, offset = pi/4, 0.05
        move_left = numpy.array([[cos(-angle), -sin(-angle), 0, offset],
                                 [sin(-angle),  cos(-angle), 0,      0],
                                 [          0,            0, 1,      0],
                                 [          0,            0, 0,      1]])
        move_right = numpy.array([[cos(angle), -sin(angle), 0, -offset],
                                  [sin(angle),  cos(angle), 0,       0],
                                  [         0,           0, 1,       0],
                                  [         0,           0, 0,       1]])
        return [center_pose,
                PoseFromMatrix(move_left*center_matrix),
                PoseFromMatrix(move_right*center_matrix)]

    def sample_bin(self, bin, poses):
        print "Reset:", self.sample(command="reset")
        for pose in poses:
            current_pose = self.arm.get_current_pose().pose
            if not follow_path(group, [current_pose, pose]):
                return False
            print "Sample:", self.sample(command=bin)
        return True
