#include <ros/ros.h>
#include <cmath>
#include <iostream>
#include <std_msgs/Float32MultiArray.h>
#include "utility.h"
#include "Hardware/can.h"
#include "Hardware/motor.h"
#include "Hardware/teleop.h"
#include "App/arm_control.h"
#include "App/arm_control.cpp"
#include "App/keyboard.h"
#include "App/play.h"
#include "App/solve.h"
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>
#include <thread>
#include <atomic>
#include "arm_control/JointControl.h"
#include "arm_control/JointInformation.h"
#include "arm_control/PosCmd.h"
#include <std_msgs/Bool.h>

int CONTROL_MODE=0; // 0 arx5 rc ，1 5a rc ，2 arx5 ros ，3 5a ros
command cmd;

float calc_cur[7]={};

int main(int argc, char **argv)
{
    ros::init(argc, argv, "arm2"); 
    ros::NodeHandle node;
    Teleop_Use()->teleop_init(node);

    arx_arm ARX_ARM((int) CONTROL_MODE);

    // 订阅 /joint_control: 仅在示教模式(human_intervention_flag)时写入关节目标, 始终读mode
    ros::Subscriber sub_joint = node.subscribe<arm_control::JointControl>("joint_control", 10,
                                  [&ARX_ARM](const arm_control::JointControl::ConstPtr& msg) {
                                      // 始终读取 mode 字段
                                      ARX_ARM.record_mode = msg->mode;
                                      // 仅在示教模式下接受关节控制
                                      if(ARX_ARM.human_intervention_flag || msg->mode == 2) {
                                          ARX_ARM.ros_control_pos_t[0] = msg->joint_pos[0];
                                          ARX_ARM.ros_control_pos_t[1] = msg->joint_pos[1];
                                          ARX_ARM.ros_control_pos_t[2] = msg->joint_pos[2];
                                          ARX_ARM.ros_control_pos_t[3] = msg->joint_pos[3];
                                          ARX_ARM.ros_control_pos_t[4] = msg->joint_pos[4];
                                          ARX_ARM.ros_control_pos_t[5] = msg->joint_pos[5];
                                          ARX_ARM.ros_control_pos_t[6] = msg->joint_pos[6];
                                      }
                                  });

    // 订阅 /follow_control: 从臂末端位姿控制(PosCmd)
    ros::Subscriber sub_follow_control = node.subscribe<arm_control::PosCmd>("/follow_control", 10,
                                  [&ARX_ARM](const arm_control::PosCmd::ConstPtr& msg) {
                                      ARX_ARM.follow_control_x = msg->x;
                                      ARX_ARM.follow_control_y = msg->y;
                                      ARX_ARM.follow_control_z = msg->z;
                                      ARX_ARM.follow_control_roll = msg->roll;
                                      ARX_ARM.follow_control_pitch = msg->pitch;
                                      ARX_ARM.follow_control_yaw = msg->yaw;
                                      ARX_ARM.follow_control_gripper = msg->gripper;
                                      ARX_ARM.use_follow_control = true;
                                  });

    // 订阅 /human_intervention: 模式切换
    ros::Subscriber sub_human_intervention = node.subscribe<std_msgs::Bool>("/human_intervention", 10,
                                  [&ARX_ARM](const std_msgs::Bool::ConstPtr& msg) {
                                      ARX_ARM.human_intervention_flag = msg->data;
                                      ROS_INFO("Follow1 Human intervention: %s", msg->data ? "TRUE" : "FALSE");
                                  });

    ros::Publisher pub_current = node.advertise<arm_control::JointInformation>("joint_information", 10);
    ros::Publisher pub_pos = node.advertise<arm_control::PosCmd>("/follow1_pos_back", 10);
    ros::Publisher pub_eclip_force = node.advertise<std_msgs::Float32MultiArray>("/follow1_eclip_force", 10);
    ros::Publisher pub_eclip_tau = node.advertise<std_msgs::Float32MultiArray>("/follow1_eclip_tau", 10);
    ros::Publisher pub_safe_pos = node.advertise<arm_control::PosCmd>("/follow1_safe_pos", 10);
    ros::Publisher pub_tool_points_world_z = node.advertise<std_msgs::Float32MultiArray>("/follow1_tool_points_world_z", 10);
    // 发布 /master_joint_control: 从臂关节位置 → 主臂跟随
    ros::Publisher pub_master_joint = node.advertise<arm_control::JointControl>("/master_joint_control", 10);
    


    arx5_keyboard ARX_KEYBOARD;

    ros::Rate loop_rate(200);
    ARX_ARM.set_loop_rate(200);
    can CAN_Handlej;

    std::thread keyThread(&arx5_keyboard::detectKeyPress, &ARX_KEYBOARD);
    sleep(1);

    while(ros::ok())
    { 

        ROS_INFO("follow1>>>>>>>>>>>>>>>>>>>>");
//程序主逻辑

        char key = ARX_KEYBOARD.keyPress.load();
        ARX_ARM.getKey(key);

        ARX_ARM.get_curr_pos();
        if(!ARX_ARM.is_starting){
             cmd = ARX_ARM.get_cmd();
        }
        ARX_ARM.update_real(cmd);

//发送关节数据
            arm_control::JointInformation msg_joint;   

            for(int i=0;i<6;i++)
            {
                msg_joint.joint_pos[i] = ARX_ARM.current_pos[i];
                msg_joint.joint_vel[i] = ARX_ARM.current_vel[i];
                msg_joint.joint_cur[i] = ARX_ARM.current_torque[i];
            }    

            msg_joint.joint_pos[6]= ARX_ARM.current_pos[6];
            msg_joint.joint_vel[6]= ARX_ARM.current_vel[6];
            if(ARX_ARM.current_vel[6]<2)
            {
                msg_joint.joint_cur[6]=-ARX_ARM.Data_process(ARX_ARM.current_torque[6]);  //0.3
            }
            else
            {
                msg_joint.joint_cur[6]=0;  //0.3
            }
            ros::Time time=ros::Time::now();
            msg_joint.header.stamp = time;
            pub_current.publish(msg_joint);

//发送末端姿态
            arm_control::PosCmd msg_pos_back;            
            msg_pos_back.x      =ARX_ARM.solve.solve_pos[0];
            msg_pos_back.y      =ARX_ARM.solve.solve_pos[1];
            msg_pos_back.z      =ARX_ARM.solve.solve_pos[2];
            msg_pos_back.roll   =ARX_ARM.solve.solve_pos[3];
            msg_pos_back.pitch  =ARX_ARM.solve.solve_pos[4];
            msg_pos_back.yaw    =ARX_ARM.solve.solve_pos[5];
            msg_pos_back.gripper=ARX_ARM.current_pos[6];
            msg_pos_back.header.stamp = time;
            pub_pos.publish(msg_pos_back);

// 发布两类eclip误差向量
            std_msgs::Float32MultiArray msg_eclip_force;
            std_msgs::Float32MultiArray msg_eclip_tau;
            msg_eclip_force.data.resize(6);
            msg_eclip_tau.data.resize(6);
            for (int i = 0; i < 6; ++i)
            {
                msg_eclip_force.data[i] = ARX_ARM.cartesian_error_clip_from_force[i];
                msg_eclip_tau.data[i] = ARX_ARM.cartesian_error_clip_from_tau[i];
            }
            pub_eclip_force.publish(msg_eclip_force);
            pub_eclip_tau.publish(msg_eclip_tau);

// 发布safe位姿
            arm_control::PosCmd msg_safe_pos;
            msg_safe_pos.x = ARX_ARM.p_safe[0];
            msg_safe_pos.y = ARX_ARM.p_safe[1];
            msg_safe_pos.z = ARX_ARM.p_safe[2];
            msg_safe_pos.roll = ARX_ARM.p_safe[3];
            msg_safe_pos.pitch = ARX_ARM.p_safe[4];
            msg_safe_pos.yaw = ARX_ARM.p_safe[5];
            msg_safe_pos.gripper = ARX_ARM.follow_control_gripper;
            msg_safe_pos.header.stamp = time;
            pub_safe_pos.publish(msg_safe_pos);

// 发布末端固连点世界系z（检验防碰地）
            std_msgs::Float32MultiArray msg_tool_points_world_z;
            msg_tool_points_world_z.data = ARX_ARM.tool_collision_points_world_z;
            pub_tool_points_world_z.publish(msg_tool_points_world_z);

//发送关节位置给主臂跟随
            arm_control::JointControl msg_master_joint;
            for(int i=0;i<7;i++)
            {
                msg_master_joint.joint_pos[i] = ARX_ARM.current_pos[i];
                msg_master_joint.joint_vel[i] = ARX_ARM.current_vel[i];
                msg_master_joint.joint_cur[i] = ARX_ARM.current_torque[i];
            }
            msg_master_joint.mode = 0;
            msg_master_joint.header.stamp = time;
            pub_master_joint.publish(msg_master_joint);


        ros::spinOnce();
        loop_rate.sleep();
        
    }

    return 0;
}