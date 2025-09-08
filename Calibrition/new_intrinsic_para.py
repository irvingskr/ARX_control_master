import pyrealsense2 as rs
import numpy as np

try:
    # 初始化相机管道
    pipeline = rs.pipeline()
    config = rs.config()
    
    # 获取连接的设备
    ctx = rs.context()
    devices = ctx.query_devices()
    if len(devices) == 0:
        print("未检测到RealSense设备")
        exit()
    
    # 打印设备信息
    for dev in devices:
        print(f"设备序列号: {dev.get_info(rs.camera_info.serial_number)}, 名称: {dev.get_info(rs.camera_info.name)}")
    
    # 选择第一个设备（或指定你想要的序列号）
    serial_number = devices[0].get_info(rs.camera_info.serial_number)
    config.enable_device(serial_number)
    
    # 配置流
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    # 启动设备
    print("正在启动相机...")
    profile = pipeline.start(config)
    print("相机启动成功")

    # 获取彩色相机的内参
    color_profile = profile.get_stream(rs.stream.color)
    color_intrinsics = color_profile.as_video_stream_profile().get_intrinsics()

    # 打印内参
    print("\n彩色相机内参：")
    print(f"焦距 (fx, fy): ({color_intrinsics.fx}, {color_intrinsics.fy})")
    print(f"主点 (cx, cy): ({color_intrinsics.ppx}, {color_intrinsics.ppy})")
    print(f"畸变模型: {color_intrinsics.model}")
    print(f"畸变系数: {np.array(color_intrinsics.coeffs)}")

    # 深度相机的内参
    depth_profile = profile.get_stream(rs.stream.depth)
    depth_intrinsics = depth_profile.as_video_stream_profile().get_intrinsics()
    print("\n深度相机内参：")
    print(f"焦距 (fx, fy): ({depth_intrinsics.fx}, {depth_intrinsics.fy})")
    print(f"主点 (cx, cy): ({depth_intrinsics.ppx}, {depth_intrinsics.ppy})")

except Exception as e:
    print(f"发生错误: {e}")
finally:
    # 停止管道
    pipeline.stop()
    print("相机已关闭")