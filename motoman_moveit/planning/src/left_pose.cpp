#include <ros/ros.h>
#include <geometry_msgs/Pose.h>

int main(int argc, char **argv)
{
  ros::init(argc, argv, "left_target_pose");
  ros::NodeHandle node_handle;  
  ros::AsyncSpinner spinner(4);
  spinner.start();

  // SET TARGET POSE VALUES


  // BIN #1
  float x = 0.1;
  float y = -0.6;  // +Z
  float z = 0.5;  // -Y
  float rx = 0;
  float ry = 0;
  float rz = 0;
  float rw = 1;


/*
  // BIN #2
  float x = 0.4;
  float y = -0.25;
  float z = 1.65;
  float rx = 0.99619468809174;
  float ry = 0.08715574274765817;
  float rz = 0;
  float rw = 0;

  // BIN #2
  float x = 0.4;
  float y = -0.25;
  float z = 1.65;
  float rx = 0;
  float ry = 0;
  float rz = 0;
  float rw = 1;
*/

/*
  // BIN #3
  float x = 0.45;
  float y = 0;
  float z = 1.65;
  float rx = 0;
  float ry = 0;
  float rz = 0;
  float rw = 1.0;


  // BIN #4
  float x = 0.35;
  float y = -0.5;
  float z = 1.4;
  float rx = 0;
  float ry = 0;
  float rz = 0;
  float rw = 1.0;


  // BIN #5
  float x = 0.4;
  float y = -0.25;
  float z = 1.0;
  float rx = 0;
  float ry = 0;
  float rz = 0;
  float rw = 1.0;


  // BIN #6
  float x = 0.45;
  float y = 0;
  float z = 1.0;
  float rx = 0;
  float ry = 0;
  float rz = 0;
  float rw = 1.0;


  // BIN #7
  float x = 0.35;
  float y = -0.5;
  float z = 1.15;
  float rx = 0;
  float ry = 0;
  float rz = 0;
  float rw = 1.0;


  // BIN #8
  float x = 0.4;
  float y = -0.25;
  float z = 1.0;
  float rx = 0;
  float ry = 0;
  float rz = 0;
  float rw = 1.0;

  // BIN #9
  float x = 0.45;
  float y = 0;
  float z = 1.0;
  float rx = 0;
  float ry = 0;
  float rz = 0;
  float rw = 1.0;


  // BIN #10
  float x = 0.35;
  float y = -0.5;
  float z = 0.9;
  float rx = 0;
  float ry = 0;
  float rz = 0;
  float rw = 1.0;


  // BIN #11
  float x = 0.4;
  float y = -0.25;
  float z = .9;
  float rx = 0;
  float ry = 0;
  float rz = 0;
  float rw = 1.0;


  // BIN #12
  float x = 0.45;
  float y = 0;
  float z = 0.9;
  float rx = 0;
  float ry = 0;
  float rz = 0;
  float rw = 1.0;
*/


  // publishers for target pose
  ros::Publisher right_publisher = node_handle.advertise<geometry_msgs::Pose>("/arm_right_target", 1, true);
  ros::Publisher left_publisher = node_handle.advertise<geometry_msgs::Pose>("/arm_left_target", 1, true);
 
  geometry_msgs::Pose target_pose;
  target_pose.position.x = x;
  target_pose.position.y = y;
  target_pose.position.z = z;
  target_pose.orientation.x = rx;
  target_pose.orientation.y = ry;
  target_pose.orientation.z = rz;
  target_pose.orientation.w = rw;


  // COMMENT OUT 1 OF THE PUBLISHERS (pick which arm you want to move)
  
//  right_publisher.publish(target_pose);
  
  left_publisher.publish(target_pose);


  while(1){}

}