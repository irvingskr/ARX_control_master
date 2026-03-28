#!/usr/bin/env bash
set -euo pipefail

WS_DIR="/home/arxpro/chenzh/ARX_control_master/follow1"

if [[ ! -f "/opt/ros/noetic/setup.bash" ]]; then
  echo "[ERROR] ROS Noetic setup not found: /opt/ros/noetic/setup.bash"
  exit 1
fi

if [[ ! -f "$WS_DIR/devel/setup.bash" ]]; then
  echo "[ERROR] Workspace setup not found: $WS_DIR/devel/setup.bash"
  echo "Build first: cd $WS_DIR && catkin_make"
  exit 1
fi

source /opt/ros/noetic/setup.bash
source "$WS_DIR/devel/setup.bash"

if ! rostopic list >/dev/null 2>&1; then
  echo "[INFO] roscore is not running, starting it..."
  roscore >/tmp/roscore_follow1.log 2>&1 &
  sleep 2
fi

if ! rostopic list | grep -q '^/follow_control$'; then
  if [[ "${1:-}" == "--mock-follow-control" ]]; then
    echo "[INFO] /follow_control missing, starting a mock publisher at 30 Hz"
    rostopic pub -r 30 /follow_control arm_control/PosCmd \
      "{x: 0.25, y: 0.0, z: 0.35, roll: 0.0, pitch: 0.0, yaw: 0.0, gripper: 0.0, mode1: 0, mode2: 0}" \
      >/tmp/follow_control_mock.log 2>&1 &
    sleep 1
  else
    echo "[WARN] /follow_control has no publisher."
    echo "       Pass --mock-follow-control to start a test publisher."
  fi
fi

echo "[INFO] Launching rqt_topic..."
rqt --standalone rqt_topic >/tmp/rqt_topic_follow1.log 2>&1 &

sleep 0.5

echo "[INFO] Launching rqt_plot (position xyz)..."
rqt_plot \
  /follow1_pos_back/x /follow1_safe_pos/x /follow_control/x \
  /follow1_pos_back/y /follow1_safe_pos/y /follow_control/y \
  /follow1_pos_back/z /follow1_safe_pos/z /follow_control/z \
  >/tmp/rqt_plot_follow1_xyz.log 2>&1 &

sleep 0.5

echo "[INFO] Launching rqt_plot (orientation rpy)..."
rqt_plot \
  /follow1_pos_back/roll /follow1_safe_pos/roll /follow_control/roll \
  /follow1_pos_back/pitch /follow1_safe_pos/pitch /follow_control/pitch \
  /follow1_pos_back/yaw /follow1_safe_pos/yaw /follow_control/yaw \
  >/tmp/rqt_plot_follow1_rpy.log 2>&1 &

sleep 0.5

echo "[INFO] Launching rqt_plot (gripper)..."
rqt_plot \
  /follow1_pos_back/gripper /follow1_safe_pos/gripper /follow_control/gripper \
  >/tmp/rqt_plot_follow1_gripper.log 2>&1 &

echo "[DONE] Visualization windows launched."
echo "       Use: pkill -f rqt_plot; pkill -f rqt_topic"
