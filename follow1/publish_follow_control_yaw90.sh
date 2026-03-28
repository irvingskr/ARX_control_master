#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./publish_follow_control_yaw90.sh            # publish continuously at 30 Hz
#   ./publish_follow_control_yaw90.sh --once     # publish only once
#   ./publish_follow_control_yaw90.sh --rate 50  # publish continuously at 50 Hz

WS_DIR="/home/arxpro/chenzh/ARX_control_master/follow1"
ROS_SETUP="/opt/ros/noetic/setup.bash"
WS_SETUP="$WS_DIR/devel/setup.bash"

RATE=30
ONCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --once)
      ONCE=1
      shift
      ;;
    --rate)
      if [[ $# -lt 2 ]]; then
        echo "[ERROR] --rate requires a number"
        exit 1
      fi
      RATE="$2"
      shift 2
      ;;
    *)
      echo "[ERROR] Unknown argument: $1"
      echo "Usage: $0 [--once] [--rate N]"
      exit 1
      ;;
  esac
done

if [[ ! -f "$ROS_SETUP" ]]; then
  echo "[ERROR] ROS setup not found: $ROS_SETUP"
  exit 1
fi
if [[ ! -f "$WS_SETUP" ]]; then
  echo "[ERROR] Workspace setup not found: $WS_SETUP"
  echo "Build first: cd $WS_DIR && catkin_make"
  exit 1
fi

source "$ROS_SETUP"
source "$WS_SETUP"

if ! rostopic list >/dev/null 2>&1; then
  echo "[ERROR] roscore is not running"
  exit 1
fi

if ! rostopic list | grep -q '^/follow1_pos_back$'; then
  echo "[ERROR] /follow1_pos_back is not available"
  echo "Start node first: rosrun arm_control arm2"
  exit 1
fi

MSG="$(rostopic echo -n 1 /follow1_pos_back)"

x="$(echo "$MSG" | awk '/^[[:space:]]*x:/{print $2; exit}')"
y="$(echo "$MSG" | awk '/^[[:space:]]*y:/{print $2; exit}')"
z="$(echo "$MSG" | awk '/^[[:space:]]*z:/{print $2; exit}')"
roll="$(echo "$MSG" | awk '/^[[:space:]]*roll:/{print $2; exit}')"
pitch="$(echo "$MSG" | awk '/^[[:space:]]*pitch:/{print $2; exit}')"
gripper="$(echo "$MSG" | awk '/^[[:space:]]*gripper:/{print $2; exit}')"

yaw="0.5708"

if [[ -z "$x" || -z "$y" || -z "$z" || -z "$roll" || -z "$pitch" || -z "$gripper" ]]; then
  echo "[ERROR] Failed to parse /follow1_pos_back"
  exit 1
fi

echo "[INFO] Current pose from /follow1_pos_back:"
echo "       x=$x y=$y z=$z roll=$roll pitch=$pitch gripper=$gripper"
echo "[INFO] Target yaw set to 90 deg (1.5708 rad)"

PAYLOAD="{x: $x, y: $y, z: $z, roll: $roll, pitch: $pitch, yaw: $yaw, gripper: $gripper, mode1: 0, mode2: 0}"

if [[ "$ONCE" -eq 1 ]]; then
  echo "[INFO] Publishing once to /follow_control"
  rostopic pub -1 /follow_control arm_control/PosCmd "$PAYLOAD"
else
  echo "[INFO] Publishing continuously to /follow_control at ${RATE} Hz"
  rostopic pub -r "$RATE" /follow_control arm_control/PosCmd "$PAYLOAD"
fi
