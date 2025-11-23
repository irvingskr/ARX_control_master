#!/home/arxpro/miniconda3/envs/dp3/bin/python
import sys
sys.path.append("/home/arxpro/miniconda3/envs/dp3/lib/python3.8/site-packages")
import zarr
from arm_control.msg import JointControl
import time
import rospy

DRY_RUN = False  # True: 只打印动作，不实际发布

dataset_path = "/home/arxpro/ARX_Remote_Control/data/test_wxp09071.zarr"
zarr_root = zarr.open(dataset_path, mode='r')
actions = zarr_root['data']['action'][:]

rospy.init_node("action_replay")
pub = rospy.Publisher("joint_control", JointControl, queue_size=10)
rate = rospy.Rate(25)  # 慢速回放

def is_safe(joint_pos):
    return True  # 取消关节限位检查，始终返回True

try:
    for i, joint_pos in enumerate(actions):
        if rospy.is_shutdown():
            break
        msg = JointControl()
        msg.joint_pos = joint_pos.tolist()
        print(f"Replay step {i+1}/{len(actions)}: {msg.joint_pos}")
        if not DRY_RUN:
            pub.publish(msg)
        rate.sleep()
        # 可加人工确认
        # input("Press Enter to continue...")
except KeyboardInterrupt:
    print("Replay interrupted by user (Ctrl+C).")

print("Replay finished.")