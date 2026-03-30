#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发布 /follow_control，实现末端相对位移的平滑控制。

用法示例：
python3 follow_control_relative_move.py \
    --dx 0.03 --dy 0.00 --dz 0.02 --duration 2.0 --hz 50
"""

import argparse
import time
import numpy as np

import rospy
from arm_control.msg import PosCmd


class FollowControlRelativeMover:
    def __init__(self, state_topic: str, control_topic: str, hz: float):
        self._state = None  # [x,y,z,roll,pitch,yaw,gripper]
        self._hz = float(hz)

        self._pub = rospy.Publisher(control_topic, PosCmd, queue_size=10)
        self._sub = rospy.Subscriber(
            state_topic, PosCmd, self._state_cb, queue_size=1
        )

    def _state_cb(self, msg: PosCmd):
        self._state = np.array(
            [msg.x, msg.y, msg.z, msg.roll, msg.pitch, msg.yaw, msg.gripper],
            dtype=np.float64,
        )

    def wait_state(self, timeout: float = 5.0):
        t0 = time.time()
        while (
            self._state is None
            and (time.time() - t0) < timeout
            and not rospy.is_shutdown()
        ):
            rospy.sleep(0.01)
        if self._state is None:
            raise RuntimeError("未收到状态话题，无法执行相对运动")

    def _publish_pose(self, pose7: np.ndarray):
        msg = PosCmd()
        msg.x = float(pose7[0])
        msg.y = float(pose7[1])
        msg.z = float(pose7[2])
        msg.roll = float(pose7[3])
        msg.pitch = float(pose7[4])
        msg.yaw = float(pose7[5])
        msg.gripper = float(pose7[6])
        msg.mode1 = 0
        msg.mode2 = 0
        msg.header.stamp = rospy.Time.now()
        self._pub.publish(msg)

    def smooth_relative_move(self, delta7: np.ndarray, duration: float):
        if duration <= 0:
            raise ValueError("duration 必须 > 0")

        self.wait_state()
        start_pose = self._state.copy()
        target_pose = start_pose + delta7

        steps = max(2, int(duration * self._hz))
        rate = rospy.Rate(self._hz)

        # 余弦插值（比线性更平滑）
        for i in range(steps):
            if rospy.is_shutdown():
                return
            s = i / float(steps - 1)
            alpha = 0.5 - 0.5 * np.cos(np.pi * s)
            cmd_pose = (1.0 - alpha) * start_pose + alpha * target_pose
            self._publish_pose(cmd_pose)
            rate.sleep()

        # 保持目标若干帧，降低末端抖动
        for _ in range(10):
            if rospy.is_shutdown():
                return
            self._publish_pose(target_pose)
            rate.sleep()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state_topic", type=str, default="/follow1_pos_back")
    parser.add_argument("--control_topic", type=str, default="/follow_control")
    parser.add_argument("--hz", type=float, default=50.0)
    parser.add_argument("--duration", type=float, default=2.0)

    parser.add_argument("--dx", type=float, default=0.0)
    parser.add_argument("--dy", type=float, default=0.0)
    parser.add_argument("--dz", type=float, default=0.0)
    parser.add_argument("--droll", type=float, default=0.0)
    parser.add_argument("--dpitch", type=float, default=0.0)
    parser.add_argument("--dyaw", type=float, default=0.0)
    parser.add_argument("--dgripper", type=float, default=0.0)

    args = parser.parse_args()

    rospy.init_node("follow_control_relative_move", anonymous=True)

    mover = FollowControlRelativeMover(
        state_topic=args.state_topic,
        control_topic=args.control_topic,
        hz=args.hz,
    )

    delta = np.array(
        [
            args.dx,
            args.dy,
            args.dz,
            args.droll,
            args.dpitch,
            args.dyaw,
            args.dgripper,
        ],
        dtype=np.float64,
    )

    rospy.loginfo(
        (
            "开始相对运动: "
            "delta=[%.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f], "
            "duration=%.2fs"
        ),
        delta[0],
        delta[1],
        delta[2],
        delta[3],
        delta[4],
        delta[5],
        delta[6],
        args.duration,
    )

    try:
        mover.smooth_relative_move(delta, args.duration)
        rospy.loginfo("相对运动完成")
    except Exception as e:
        rospy.logerr("执行失败: %s", str(e))


if __name__ == "__main__":
    main()
