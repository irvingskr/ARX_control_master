workspace=$(pwd)

# 启动第一个 follow1 文件
gnome-terminal -- bash -c "cd ${workspace}/follow1 && source devel/setup.bash && cd ${workspace}/follow1/src/arm_control/scripts && conda run -n dp3 python back_to_origin.py"
