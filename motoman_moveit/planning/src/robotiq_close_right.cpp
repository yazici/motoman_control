#include <ros/ros.h>
#include <sensor_msgs/JointState.h>
//#include <trajectory_msgs/JointTrajectory.h>
//#include <trajectory_msgs/JointTrajectoryPoint.h>
//#include <string>


  sensor_msgs::JointState jointGoals;

void read_joints(sensor_msgs::JointState msg)
{




  jointGoals.header = msg.header;
  jointGoals.name = msg.name;
  jointGoals.position = msg.position;
  jointGoals.velocity = msg.velocity;

  jointGoals.position[0] = 0;
  jointGoals.position[1] = 0;
  jointGoals.position[2] = 0;
  jointGoals.position[3] = 0;
  jointGoals.position[4] = 0;
  jointGoals.position[5] = 0;
  jointGoals.position[6] = 0;
  jointGoals.position[7] = 0;
  jointGoals.position[8] = 0;
  jointGoals.position[9] = 0;
  jointGoals.position[10] = 0;
  jointGoals.position[11] = 0;
  jointGoals.position[12] = 0;
  jointGoals.position[13] = 0;
  jointGoals.position[14] = 0;
  jointGoals.position[15] = 0;
  jointGoals.position[16] = 0;
  jointGoals.position[17] = 0;
  jointGoals.position[18] = 0;
  jointGoals.position[19] = 0;
  jointGoals.position[20] = 0;
  jointGoals.position[21] = 0;
  jointGoals.position[22] = 0;
  jointGoals.position[23] = 0;
  jointGoals.position[24] = 0;
  jointGoals.position[25] = 0;
  jointGoals.position[26] = 1.0;
  jointGoals.position[27] = 1.0;
  jointGoals.position[28] = 1.0;
  jointGoals.position[29] = 1.0;
  jointGoals.position[30] = 1.0;
  jointGoals.position[31] = 1.0;
  jointGoals.position[32] = 1.0;
  jointGoals.position[33] = 1.0;
  jointGoals.position[34] = 1.0;
  jointGoals.position[35] = 1.0;
  jointGoals.position[36] = 1.0;
  jointGoals.position[37] = 1.0;



}


int main(int argc, char **argv)
{
  ros::init(argc, argv, "robotiq_close_right");
  ros::NodeHandle node_handle;  
  ros::AsyncSpinner spinner(4);
  spinner.start();

  ros::Subscriber right_sub = node_handle.subscribe("/joint_states", 1, read_joints);

  ros::Publisher right_hand_publisher = node_handle.advertise<sensor_msgs::JointState>("/move_group/fake_controller_joint_states", 1, true);


  //sensor_msgs::JointState jointGoals;
  //jointGoals.header.stamp = ros::Time::now();
  //jointGoals.name.std::append( "hand_right_palm_finger_1_joint");
/*  jointGoals.position[0] = 2.0;
  jointGoals.name[1] = "hand_right_finger_1_joint_1";
  jointGoals.position[1] = 2.0;
  jointGoals.name[2] = "hand_right_finger_1_joint_2";
  jointGoals.position[2] = 2.0;
  jointGoals.name[3] = "hand_right_finger_1_joint_3";
  jointGoals.position[3] = 2.0;
  jointGoals.name[4] = "hand_right_palm_finger_2_joint";
  jointGoals.position[4] = 2.0;
  jointGoals.name[5] = "hand_right_finger_2_joint_1";
  jointGoals.position[5] = 2.0;
  jointGoals.name[6] = "hand_right_finger_2_joint_2";
  jointGoals.position[6] = 2.0;
  jointGoals.name[7] = "hand_right_finger_2_joint_3";
  jointGoals.position[7] = 2.0;
  jointGoals.name[8] = "hand_right_palm_finger_middle_joint";
  jointGoals.position[8] = 2.0;
  jointGoals.name[9] = "hand_right_finger_middle_joint_1";
  jointGoals.position[9] = 2.0;
  jointGoals.name[10] = "hand_right_finger_middle_joint_2";
  jointGoals.position[10] = 2.0;
  jointGoals.name[11] = "hand_right_finger_middle_joint_3";*/
  //jointGoals.position.std::append( 2.0);


  // publisher for right hand
  
  
 

  while(1){
    
  right_hand_publisher.publish(jointGoals);
    //ros::Duration(0.1).sleep();
  }

}