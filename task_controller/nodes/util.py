
import rospy

from geometry_msgs.msg import PoseStamped

def goto_pose(group, pose, times=[5, 20, 40, 60]):
    for t in times:
        group.set_planning_time(t)
        rospy.loginfo("Planning for "+str(t)+" seconds...")
        result = group.go(pose)
        if result:
            return True
    return False

def follow_path(group, path, collision_checking=True):
    traj, success = group.compute_cartesian_path(
        path,
        0.01, # 1cm interpolation resolution
        0.0, # jump_threshold disabled
        avoid_collisions = collision_checking,
    )
    if success < 1:
        rospy.logwarn("Cartesian trajectory could not be completed. Only solved for: '"+str(success)+"'...")
        return False
    return group.execute(traj)

def bin_pose(bin, bin_x=1.32, bin_y=0, bin_z=-0.01):
    # Setting Configuration:
    # 	A		B		C
    # 	D		E		F
    # 	G		H		I
    # 	J		K		L
    # 		   Base

    # Gripper dimension
    GripperLength = 0.2

    # Bin dimension Unit m
    Bin_depth = 0.430
    Start_Gap = 0.100

    LeftBin_width = 0.240
    MiddleBin_width = 0.300
    RightBin_width = 0.240

    WorkBase_Height = 0.820
    BottomLay_Height = 0.230
    SecndLayer_Height = 0.230
    ThirdLayer_Height = 0.220
    TopLayer_Height = 0.260

    Left_horizontal_ShiftValue = MiddleBin_width/2 + LeftBin_width/2
    Right_horizontal_ShiftValue = MiddleBin_width/2 + RightBin_width/2

    TopLayer_vertical_shiftvalue = WorkBase_Height + BottomLay_Height + SecndLayer_Height + ThirdLayer_Height + TopLayer_Height/2
    ThirdLayer_vertical_shiftvalue = WorkBase_Height + BottomLay_Height + SecndLayer_Height + ThirdLayer_Height/2
    SecndLayer_vertical_shiftvalue = WorkBase_Height + BottomLay_Height + SecndLayer_Height/2
    BottomLayer_vertical_shiftvalue = WorkBase_Height + BottomLay_Height/2

    Entry_X_shiftvalue = bin_x - Bin_depth - Start_Gap - GripperLength - 0.035

    pose = PoseStamped()
    pose.pose.position.x = Entry_X_shiftvalue

    if bin == "A":
        pose.pose.position.y = bin_y + Left_horizontal_ShiftValue
        pose.pose.position.z = bin_z + TopLayer_vertical_shiftvalue
    elif bin == "B":
        pose.pose.position.y = bin_y
        pose.pose.position.z = bin_z + TopLayer_vertical_shiftvalue
    elif bin == "C":
        pose.pose.position.y = bin_y - Right_horizontal_ShiftValue
        pose.pose.position.z = bin_z + TopLayer_vertical_shiftvalue
    elif bin == "D":
        pose.pose.position.y = bin_y + Left_horizontal_ShiftValue
        pose.pose.position.z = bin_z + ThirdLayer_vertical_shiftvalue
    elif bin == "E":
        pose.pose.position.y = bin_y
        pose.pose.position.z = bin_z + ThirdLayer_vertical_shiftvalue
    elif bin == "F":
        pose.pose.position.y = bin_y - Right_horizontal_ShiftValue
        pose.pose.position.z = bin_z + ThirdLayer_vertical_shiftvalue
    elif bin == "G":
        pose.pose.position.y = bin_y + Left_horizontal_ShiftValue
        pose.pose.position.z = bin_z + SecndLayer_vertical_shiftvalue
    elif bin == "H":
        pose.pose.position.y = bin_y
        pose.pose.position.z = bin_z + SecndLayer_vertical_shiftvalue
    elif bin == "I":
        pose.pose.position.y = bin_y - Right_horizontal_ShiftValue
        pose.pose.position.z = bin_z + SecndLayer_vertical_shiftvalue
    elif bin == "J":
        pose.pose.position.y = bin_y + Left_horizontal_ShiftValue
        pose.pose.position.z = bin_z + BottomLayer_vertical_shiftvalue
    elif bin == "K":
        pose.pose.position.y = bin_y
        pose.pose.position.z = bin_z + BottomLayer_vertical_shiftvalue
    elif bin == "L":
        pose.pose.position.y = bin_y - Right_horizontal_ShiftValue
        pose.pose.position.z = bin_z + BottomLayer_vertical_shiftvalue
    else:
        raise Exception("Bin `%s` not supported."%bin)
        # TODO: Throw exception

    #pose.pose.orientation.x = -0.12384;
    #pose.pose.orientation.y = 0.0841883;
    #pose.pose.orientation.z = -0.730178;
    #pose.pose.orientation.w = 0.666646;
    #pose.pose.orientation.x = 0.5
    #pose.pose.orientation.y = -0.5
    #pose.pose.orientation.z = -0.5
    #pose.pose.orientation.w = 0.5
    pose.pose.orientation.x = -0.484592
    pose.pose.orientation.y = 0.384602
    pose.pose.orientation.z = 0.615524
    pose.pose.orientation.w = -0.488244

    return pose