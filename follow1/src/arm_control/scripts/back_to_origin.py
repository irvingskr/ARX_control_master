#!/home/arxpro/miniconda3/envs/dp3/bin/python
import sys
sys.path.append("/home/arxpro/miniconda3/envs/dp3/lib/python3.8/site-packages")
import rospy
from arm_control.msg import JointControl, JointInformation
import numpy as np
import time

origin_joint_pos = np.array([-0.00057220458984375, 0.00743865966796875, 0.00743865966796875, 0.044823646545410156, 0.02269744873046875, 0.02536773681640625, -0.038909912109375])  # 修改为你的原点
step_num = 150  # 插值步数，越大越慢越安全

rospy.init_node("go_to_origin_smooth")
pub = rospy.Publisher("joint_control", JointControl, queue_size=10)
rate = rospy.Rate(30)  # 30Hz

# 获取当前关节状态
print("Waiting for current joint state...")
current_state = rospy.wait_for_message("joint_information", JointInformation)
current_joint_pos = np.array(current_state.joint_pos)

# 生成插值轨迹
traj = np.linspace(current_joint_pos, origin_joint_pos, step_num)

try:
    for i, pos in enumerate(traj):
        if rospy.is_shutdown():
            break
        msg = JointControl()
        msg.joint_pos = pos.tolist()
        pub.publish(msg)
        print(f"Step {i+1}/{step_num}: {msg.joint_pos}")
        rate.sleep()
except KeyboardInterrupt:
    print("Go to origin interrupted by user (Ctrl+C).")

print("Go to origin finished.")
