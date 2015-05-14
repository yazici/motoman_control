import rospy

import moveit_commander

from std_msgs.msg import Header
from sensor_msgs.msg import JointState
from shelf import Shelf, NO_SHELF, SIMPLE_SHELF, FULL_SHELF, PADDED_SHELF
from collision import scene
from trajectory_verifier.msg import CheckTrajectoryValidityQuery, CheckTrajectoryValidityResult
from services import _move, _check_collisions, _get_known_trajectory

robot = moveit_commander.RobotCommander()

LEFT_NAMES = ["torso_joint_b1", "arm_left_joint_1_s", "arm_left_joint_2_l", "arm_left_joint_3_e",
              "arm_left_joint_4_u", "arm_left_joint_5_r", "arm_left_joint_6_b", "arm_left_joint_7_t"]
LEFT_HOME = [0.0, 2.1987425554414965, -1.2856041261915816, -2.0572122610542043, -2.1844569809370875,
             -0.8355313237647156, -0.6598546685936744, 2.244587644488423]
RIGHT_NAMES = ["torso_joint_b1", "arm_right_joint_1_s", "arm_right_joint_2_l", "arm_right_joint_3_e",
              "arm_right_joint_4_u", "arm_right_joint_5_r", "arm_right_joint_6_b", "arm_right_joint_7_t"]
RIGHT_HOME = [0.0, -1.0030564513590334, -1.49978651413566, 0.457500317369117, -2.1772162870743323,
              0.4509681667487428, -1.2043397683221861, -1.5581499385881046]


def move(group, traj):
    try:
        if not check_joint_values(group, traj.joint_names, traj.points[0].positions):
            rospy.logerr("Not moving since initial joint values are not within tolerance")
            return False
        print traj
        result = _move(traj)
        if not check_joint_values(group, traj.joint_names, traj.points[-1].positions):
            rospy.logerr("Moving failed, final joint values are not within tolerance")
            return False
        return result.success
    except rospy.ServiceException as e:
        rospy.logerr("Failure with move(<<trajectory>>): %s" % (str(e)))
        return False


def check_collisions(query):
    for i in range(5):
        try:
            result = _check_collisions(query)
            return result, True
        except rospy.ServiceException as e:
            rospy.logwarn("Failure with check_collisions(<<query>>): %s" % (str(e)))
    rospy.logerr("Failed to check collisions")
    return None, False


def get_known_trajectory(task, bin):
    for i in range(5):
        try:
            result = _get_known_trajectory(task=task, bin_num=bin)
            return result.plan, True
        except rospy.ServiceException as e:
            rospy.logwarn("Failure with get_known_trajectory(%s, %s): %s" % (task, bin, str(e)))
    rospy.logerr("Failed to get known trajectory")
    return None, False


def goto_pose(group, pose, times=[5, 20, 40, 60], shelf=SIMPLE_SHELF):
    """Moves the hand to a given `pose`, using the configured `group`. The
    planning time is modified based on the passed in `times` to try to
    plan quickly if possible, but fall back on longer plans if
    necessary. If `add_shelf` is true, a box model of the shelf is
    added to the environment to avoid collisions."""
    # group.set_planner_id("RRTstarkConfigDefault")
    # group.set_planner_id("KPIECEkConfigDefault")
    group.set_planner_id("RRTConnectkConfigDefault")

    group.set_workspace([-3, -3, -3, 3, 3, 3])
    with shelf:
        for t in times:
            group.set_planning_time(t)
            rospy.loginfo("Planning for "+str(t)+" seconds...")
            plan = group.plan(pose)
            if len(plan.joint_trajectory.points) > 0:
                if move(group, plan.joint_trajectory):
                    return True
                else:
                    rospy.logwarn("Failed to execute")
            else:
                rospy.logwarn("Failed to plan in %s seconds" % t)
        rospy.logerr("Failed to go to %s" % pose)
        return False


def follow_path(group, path, collision_checking=True):
    """Follows a cartesian path using a linear interpolation of the given
    `path`. The `collision_checking` parameter controls whether or not
    to check the path for collisions with the environment."""
    traj, success = group.compute_cartesian_path(
        path,
        0.01,  # 1cm interpolation resolution
        0.0,  # jump_threshold disabled
        avoid_collisions=collision_checking,
    )

    if success < 1:
        rospy.logerr(
            "Cartesian trajectory could not be completed. Only solved for: '"
            + str(success) + "'..."
        )
        return False

    if move(group, traj.joint_trajectory):
        return True
    else:
        rospy.logerr("Failed to execute cartesian path")
        return False


def execute_known_trajectory(group, task, bin):
    plan, success = get_known_trajectory(task, bin)
    if not success:
        return False

    start = list(plan.joint_trajectory.points[0].positions)
    if group.get_current_joint_values() != start:
        rospy.logwarn("execute_known_trajectory(%s, %s): Not starting at the beginning." % (task, bin))
        if not goto_pose(group, start, [2, 2, 5, 10]):
            return False

    with SIMPLE_SHELF:
        collisions, success = check_collisions(CheckTrajectoryValidityQuery(
            initial_state=JointState(
                header=Header(stamp=rospy.Time.now()),
                name=robot.sda10f.get_joints(),
                position=robot.sda10f.get_current_joint_values()
            ),
            trajectory=plan.joint_trajectory,
            check_type=CheckTrajectoryValidityQuery.CHECK_ENVIRONMENT_COLLISION,
        ))
    if not success:
        return False
    if collisions.result.status != CheckTrajectoryValidityResult.SUCCESS:
        rospy.logwarn("Can't execute path from trajectory library, status=%s" % collisions.result.status)
        return False

    if move(group, plan.joint_trajectory):
        return True
    else:
        rospy.logerr("Failed to execute known trajectory")
        return False


def go_home(max_tries=None):
    check_left = lambda: check_joint_values(robot.arm_left_torso, LEFT_NAMES, LEFT_HOME)
    check_right = lambda: check_joint_values(robot.arm_right_torso, RIGHT_NAMES, RIGHT_HOME)
    tries = 0
    while not check_left() or not check_right():
        tries += 1
        if max_tries is not None and tries > max_tries:
            rospy.logerr("Failed to move to the home position within %s tries." % max_tries)
            return False
        if tries == 1:
            rospy.loginfo("Trying to move home")
        elif tries < 5:
            rospy.logwarn("Not currently at home position, trying to move there...")
        else:
            rospy.logerr("Not currently at home position, trying again..")

        if not check_left():
            if not goto_pose(robot.arm_left_torso, LEFT_HOME, [2, 2, 5, 10, 30]):
                rospy.logerr("Failed to move left hand to home")

        if not check_right():
            if not goto_pose(robot.arm_right_torso, RIGHT_HOME, [2, 2, 5, 10, 30]):
                rospy.logerr("Failed to move right hand to home")

    rospy.loginfo("Successfully moved home")
    return True


def check_joint_values(group, name, desired_values, tolerance=0.01):
    actual = {name: value for name, value in
              zip(group.get_joints(), group.get_current_joint_values())}

    for name, value in zip(name, desired_values):
        if abs(actual[name] - value) > tolerance:
            rospy.logerr("Joint %s should have value '%s', but has value '%s'"
                         % (name, value, actual[name]))
            return False

    return True
