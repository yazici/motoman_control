import rospy
import smach
from copy import deepcopy

from apc_util.moveit import scene, execute_known_trajectory
from apc_util.grasping import gripper
from apc_util.shelf import BIN
from apc_util.smach import on_exception


class PlaceItem(smach.State):
    """
    Place the item in the bin for shipping
    """

    def __init__(self, robot):
        smach.State.__init__(self, outcomes=['Success', 'Failure', 'Fatal'],
                             input_keys=['bin'], output_keys=[])
        self.arm = robot.arm_left_torso

    @on_exception(failure_state="Failure")
    def execute(self, userdata):
        rospy.loginfo("Trying to place from bin '"+userdata.bin+"'...")

        # rospy.sleep(4)
        from apc_util.moveit import goto_pose, follow_path
        from geometry_msgs.msg import Pose, Point, Quaternion
        target = Pose(
            position=Point(x=0.4062, y=0.43, z=0.85),
            orientation=Quaternion(x=-0.12117, y=0.49833, z=0.85847, w=0.0020136)
            # position=Point(x=0.50071, y=0.048405, z=0.97733),
            # orientation=Quaternion(x=-0.0042023, y=-0.008732, z=-0.80657, w=0.59106)
        )
        if not goto_pose(self.arm, target, [2, 2, 5, 10, 30], shelf=BIN(userdata.bin)):
            return 'Failure'

        poses = [target]
        poses.append(deepcopy(poses[-1]))
        poses[-1].position.z -= 0.15
        if not follow_path(self.arm, poses, False):
            return 'Failure'

        # with BIN(userdata.bin):
        #     if not execute_known_trajectory(self.arm, "Drop", userdata.bin):
        #         return "Failure"

        if not gripper.open():
            return "Failure"

        poses.reverse()
        if not follow_path(self.arm, poses, False):
            return 'Failure'

        scene.remove_attached_object("arm_left_link_7_t")
        return 'Success'
