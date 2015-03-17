#include <ros/ros.h>
#include <moveit/move_group_interface/move_group.h>
#include <moveit_msgs/DisplayTrajectory.h>
#include <geometry_msgs/Pose.h>
#include <geometry_msgs/PoseStamped.h>
#include <iostream>

#include <motoman_moveit/move_group_server.h>

// currently this function takes a Pose and tells the right end-effector to move there
bool move_callback(motoman_moveit::move_group_server::Request &req,
    motoman_moveit::move_group_server::Response &res)
{
	std::cout << "PLANNING..." << std::endl;
    moveit::planning_interface::MoveGroup move_group(req.arm);
    move_group.setPlannerId("RRTstarkConfigDefault");
	move_group.setPlanningTime(30.0);
	move_group.setStartStateToCurrentState();
	
	if (req.tolerance) {
		move_group.setGoalOrientationTolerance(0.2);
		move_group.setGoalPositionTolerance(0.02);
	}
	
    move_group.setPoseTarget(req.pose.pose);

    // compute and visualize plan
    moveit::planning_interface::MoveGroup::Plan plan;
    //bool success = move_group.plan(plan);
    
    std::cout << "VISUALIZING..." << std::endl;
    
    // Sleep while plan is shown in Rviz
    //sleep(10.0);

    std::cout << "MOVING..." << std::endl;
    
    // move to target pose
    //res.success = move_group.execute(plan);
	res.success = move_group.move();
	std::cout << "Executed!" << std::endl;
	
	std::cout << "ENDED!" << std::endl;

    return true;
}
    
int main(int argc, char **argv) {
    ros::init(argc, argv, "move_group_server");
    ros::NodeHandle node_handle;
    
    ros::ServiceServer service = node_handle.advertiseService("move_group_service", move_callback);
    ros::MultiThreadedSpinner spinner(4);
    spinner.spin();

    return 0;
}
