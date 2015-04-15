#include <ros/ros.h>
#include <geometry_msgs/Pose.h>
#include <motoman_moveit/move_group_server.h>
#include <apc_vision/ObjectDetect.h>
#include <grasp_logic/grasp.h>
#include <gripper_srv/gripper.h>
#include <trajectory_srv/task.h>
#include <iostream>
#include <moveit/move_group_interface/move_group.h>

#include <geometry_msgs/Pose.h>
#include <shape_msgs/SolidPrimitive.h>
#include <moveit_msgs/CollisionObject.h>
#include <moveit/planning_scene/planning_scene.h>

int main(int argc, char **argv) {
    ros::init(argc, argv, "right_target_pose");
    ros::NodeHandle node_handle;  
    ros::AsyncSpinner spinner(4);
    spinner.start();
    
    ros::service::waitForService("move_group_service");
    ros::service::waitForService("object_detect");
    ros::service::waitForService("grasp_logic");
    ros::service::waitForService("command_gripper");
    //ros::service::waitForService("trajectory_execute");
    std::cout << "SERVICES STARTED!" << std::endl;
    for (int i = 0; i < 60; i++) { 
		sleep(1.0);
		std::cout << i << " seconds" << std::endl;
	}
    std::cout << "-------DONE SLEEPING----" << std::endl;
    
    /*
    moveit_msgs::CollisionObject wall;
    wall.operation = moveit_msgs::CollisionObject::ADD;
    wall.id = "wall";
    
    shape_msgs::SolidPrimitive wallPrim;
    wallPrim.type = shape_msgs::SolidPrimitive::BOX;
    wallPrim.dimensions.push_back(0.01);
    wallPrim.dimensions.push_back(5); 
    wallPrim.dimensions.push_back(3);
    geometry_msgs::Pose wallPose;
    wallPose.position.x = -.8;
    wallPose.position.z = 1.5;
    wall.primitives.push_back(wallPrim);
    wall.primitive_poses.push_back(wallPose);
    planning_scene::PlanningScene scene;
    scene.processCollisionObjectMsg(wall);
    */
    gripper_srv::gripper act_gripper;
    act_gripper.request.command = "activate";
    
    ros::service::call("command_gripper", act_gripper);
    
    if(!act_gripper.response.status) {
		std::cout << "Activating gripper failed!" << std::endl;
		return 0;
	}
	
	gripper_srv::gripper pinch_gripper;
    pinch_gripper.request.command = "basic";
    
    ros::service::call("command_gripper", pinch_gripper);
    
    if(!pinch_gripper.response.status) {
		std::cout << "Pinch gripper failed!" << std::endl;
		return 0;
	}
    
    // activate gripper
    // ADD LATER
    
    // move to pose in front of bin
    motoman_moveit::move_group_server moveBin;    

    geometry_msgs::PoseStamped target_pose_stamped;    
    geometry_msgs::Pose target_pose;
    target_pose.position.x = 0.545954;
    target_pose.position.y = 0.0340763;
    target_pose.position.z = 1.59295;
    target_pose.orientation.x = -0.12384;
    target_pose.orientation.y = 0.0841883;
    target_pose.orientation.z = -0.730178;
    target_pose.orientation.w = 0.666646;

    target_pose_stamped.pose = target_pose;

    moveBin.request.pose = target_pose_stamped;
    moveBin.request.arm = "arm_left";

    ros::service::call("move_group_service", moveBin);
    
    while (!moveBin.response.success) {
		std::cout << "move_group_service service returned failure" << "/n";
		return 0;
	}
	std::cout << "##### Moved to bin ######" << std::endl;
/*
    std::cout << "Sending message to trajectory server" << std::endl;
    trajectory_srv::task bin_traj;
    bin_traj.request.task = "Forward";
    bin_traj.request.bin_num = "B";
    ros::service::call("trajectory_execute", bin_traj);

    if(!bin_traj.response.status) {
        std::cout << "trajectory_execute service returned failure" << std::endl;
        return 0;    
    }   

    moveit::planning_interface::MoveGroup group("arm_left");
    std::vector<double> joints = group.getCurrentJointValues();
*/
    // call vision service
    apc_vision::ObjectDetect detect;


	detect.response.found = false;

    while (!detect.response.found) {
		detect.request.bin = "B";
		detect.request.object = "expo_dry_erase_board_eraser";
		detect.response.found = false;
		std::cout << "RUNNING VISION" << std::endl;
		ros::service::call("object_detect", detect);
	}

	std::cout << "###### Found object #######" << std::endl;

    // call grasp logic service
    grasp_logic::grasp grasp;

    grasp.request.object = "elmers_washable_no_run_school_glue";
    grasp.request.obj_pose = detect.response.pose;

    ros::service::call("grasp_logic", grasp);

	std::cout << "####### Found grasp #######" << std::endl;
	
    // move to object    
    motoman_moveit::move_group_server moveObject;   

    moveObject.request.pose = grasp.response.arm_pose;
    moveObject.request.arm = "arm_left";
    //moveObject.request.tolerance = true;

    ros::service::call("move_group_service", moveObject);
    
    if (!moveObject.response.success) {
		std::cout << "move_group_service service returned failure" << "/n";
		return 0;
	}
	
	std::cout << "###### Moved to object #######" << std::endl;


    // call gripper (close) service
    gripper_srv::gripper close_gripper;
    close_gripper.request.command = "close";
    ros::service::call("command_gripper", close_gripper);
    
	if(!close_gripper.response.status) {
		std::cout << "Failed to close gripper" << std::endl;
		return 0;
	}

    // move up
    motoman_moveit::move_group_server moveUp;   

    moveUp.request.pose = grasp.response.arm_pose;
    moveUp.request.pose.pose.position.z += 0.03;    
    moveUp.request.arm = "arm_left";

    ros::service::call("move_group_service", moveUp);
    
    if (!moveUp.response.success) {
		std::cout << "move_group_service service returned failure" << "/n";
		// return 0;
	}
	
	std::cout << "###### Moved up ######" << std::endl;
/*
    group.setJointValueTarget(joints);
    group.move();

    trajectory_srv::task drop_traj;
    drop_traj.request.task = "Drop";
    drop_traj.request.bin_num = "B";

    ros::service::call("trajectory_execute", drop_traj);

    if(!drop_traj.response.status) {
        std::cout << "trajectory execute returned failure" << std::endl;
        return 0;    
    }
*/
    // move out (to same pose in front of bin)
    ros::service::call("move_group_service", moveBin);
    
    if (!moveBin.response.success) {
		std::cout << "move_group_service service returned failure" << "/n";
		return 0;
	}
	
	std::cout << "####### Moved to bin ########" << std::endl;


/*
    // move to order waypoint
    motoman_moveit::move_group_server moveWaypoint;   

    geometry_msgs::PoseStamped waypoint_pose_stamped;    
    geometry_msgs::Pose waypoint_pose;
    waypoint_pose.position.x = 0.444803;
    waypoint_pose.position.y = 0.520884;
    waypoint_pose.position.z = 0.820814;
    waypoint_pose.orientation.x = -0.146351;
    waypoint_pose.orientation.y = -0.0633737;
    waypoint_pose.orientation.z = -0.821224;
    waypoint_pose.orientation.w = 0.547866;

    waypoint_pose_stamped.pose = waypoint_pose;

    moveWaypoint.request.pose = waypoint_pose_stamped;
    moveWaypoint.request.arm = "arm_left";

    //ros::service::call("move_group_service", moveWaypoint);
    
    //if (!moveWaypoint.response.success) {
	//	std::cout << "move_group_service service returned failure" << "/n";
	//	return 0;
	//}
	std::cout << "###### Moved to waypoint ######" << std::endl;
	*/




    // move to order box
    motoman_moveit::move_group_server moveBox;   

    geometry_msgs::PoseStamped box_pose_stamped;    
    geometry_msgs::Pose box_pose;
    box_pose.position.x = -0.0245724;
    box_pose.position.y = 0.679758;
    box_pose.position.z = 0.51537;
    box_pose.orientation.x = -0.696986;
    box_pose.orientation.y = -0.225653;
    box_pose.orientation.z = 0.246046;
    box_pose.orientation.w = 0.634628;

    box_pose_stamped.pose = box_pose;

    moveBox.request.pose = box_pose_stamped;
    moveBox.request.arm = "arm_left";

/*
    ros::service::call("move_group_service", moveBox);
    
    if (!moveBox.response.success) {
		std::cout << "move_group_service service returned failure" << "/n";
		return 0;
	}*/

    moveit::planning_interface::MoveGroup move_group("arm_left");
    move_group.setPoseTarget(box_pose);
    move_group.setPlannerId("RRTstarkConfigDefault");
	move_group.setPlanningTime(90.0);
    move_group.move();
    
	
	std::cout << "###### Moved to box ######" << std::endl;


    gripper_srv::gripper open_gripper;
    open_gripper.request.command = "open";
    
    ros::service::call("command_gripper", open_gripper);
    
    if(!open_gripper.response.status) {
		std::cout << "Open gripper failed!" << std::endl;
		return 0;
	}
}