workspace=$(pwd)

# 启动第一个 follow1 文件
gnome-terminal -- bash -c "cd ${workspace}/follow1 && source devel/setup.bash && roslaunch arm_control arx5v.launch"


sleep 0.5
gnome-terminal -- bash -c "cd ${workspace}/follow1 && source devel/setup.bash && roslaunch arm_control camera.launch"