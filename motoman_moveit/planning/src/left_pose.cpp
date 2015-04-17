#include <ros/ros.h>
#include <geometry_msgs/Pose.h>

int main(int argc, char **argv)
{
  ros::init(argc, argv, "left_target_pose");
  ros::NodeHandle node_handle;  
  ros::AsyncSpinner spinner(4);
  spinner.start();

  // SET TARGET POSE VALUES

  float x = 0.1;
  float y = -0.6; 
  float z = 0.5;  
  float rx = 0;
  float ry = 0;
  float rz = 0;
  float rw = 1;


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
  
  left_publisher.publish(target_pose);


  while(1){}

}