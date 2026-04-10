# HDF5 Collection 说明

## 结论

当前项目 **仍然可以使用 HDF5 格式采集数据**，因为仓库里保留了多份基于 `h5py` 的采集脚本；但需要注意：

- **当前默认主采集脚本已经切到 Zarr**：`follow1/src/arm_control/scripts/sample.py`
- **HDF5 采集链路属于旧方案/兼容方案**：仍可运行，但不是当前默认主格式

也就是说：

> 如果你想继续采集为 `.hdf5`，是可以的，但建议明确使用哪一个 HDF5 脚本，并先检查脚本里的硬编码路径、topic、步数和相机配置。

---

## 代码依据

以下脚本仍然显式写入 `.hdf5`：

- `follow1/src/arm_control/scripts/sample_human.py`
- `follow1/src/arm_control/scripts/sample_ik.py`
- `follow1/src/arm_control/scripts/sample_initial.py`
- `follow1/src/arm_control/scripts/sample_ik_2_scene.py`
- `follow1/src/arm_control/scripts/sample_ik_3_prep.py`
- `follow1/src/arm_control/scripts/random_sample_ik_3_prep.py`
- `follow1/src/arm_control/scripts/calib_sample_ik.py`

这些脚本都包含：

- `extension = '.hdf5'`
- `dataset_path = f'{directory_path}/episode_{episode_idx}.hdf5'`
- `with h5py.File(dataset_path, 'w', ...) as root:`

说明它们仍然是可写 HDF5 的。

---

## 当前推荐理解

### 1. 默认主链路

当前主链路是：

- `follow1/src/arm_control/scripts/sample.py`
- 输出为：`xxx.zarr`

### 2. HDF5 链路

HDF5 仍然存在，适合：

- 兼容旧训练/旧处理脚本
- 做单 episode 采集
- 做简化版本采集
- 标定或特定任务的专项采集

---

## 常见 HDF5 脚本及用途

### `sample_initial.py`
较标准的双目/双相机 HDF5 采集脚本。

典型字段：

- `/observations/qpos`
- `/action`
- `/eef_qpos`
- `/observations/images/mid`
- `/observations/images/right`

输出：

- `episode_x.hdf5`
- 对应拼接视频 `video/xxxvideo.mp4`

适合：

- 普通遥操作采集
- 需要 mid + right 图像的场景

---

### `sample_ik.py`
较简化版本，通常只采集单路 `mid` 图像。

典型字段：

- `/observations/qpos`
- `/action`
- `/eef_qpos`
- `/observations/images/mid`

适合：

- 快速测试
- 简化采集
- 只保留一台相机的场景

---

### `sample_ik_2_scene.py`
双相机场景采集版本。

典型字段：

- `/observations/qpos`
- `/action`
- `/eef_qpos`
- `/observations/images/mid`
- `/observations/images/right`

适合：

- 两视角任务场景采集

---

### `sample_ik_3_prep.py`
三相机版本。

典型字段：

- `/observations/qpos`
- `/action`
- `/eef_qpos`
- `/observations/images/mid`
- `/observations/images/right`
- `/observations/images/left`

适合：

- 三视角任务采集
- 前处理/多视角准备数据

---

### `random_sample_ik_3_prep.py`
三相机随机采样版本。

特点：

- 没有标准 `/action` 字段（脚本里注释掉了）
- 会根据 qpos 变化阈值过滤重复帧

适合：

- 随机探索数据
- 稀疏采样数据

---

### `calib_sample_ik.py`
标定/ArUco 采集版本。

典型字段：

- `/observations/qpos`
- `/observations/action`
- `/observations/eef_qpos`
- `/observations/images/mid`
- `/observations/marker_poses`

特点：

- 按 **Enter** 键触发保存
- 只有检测到 ArUco 时才记录
- 字段路径和其他 HDF5 脚本不完全一致

适合：

- 手眼标定
- 标记板位姿采集

---

### `sample_human.py`
人演示/简单视频记录版本。

目前主要保存：

- `/observations/images/mid`

适合：

- 人工演示视频记录
- 仅图像数据采集

---

## HDF5 文件的典型结构

大多数 HDF5 脚本写出的结构类似：

```text
episode_x.hdf5
├── observations
│   ├── qpos                  # (T, 7)
│   └── images
│       ├── mid               # (T, 480, 640, 3), uint8
│       ├── right             # 可选
│       └── left              # 可选
├── action                    # (T, 7) 或在 observations 下
├── eef_qpos                  # (T, 7) 或在 observations 下
└── attrs['sim'] = True
```

但要注意：**不同 HDF5 脚本的字段路径并不完全统一**。

例如：

- 多数脚本把 `action` / `eef_qpos` 放在 **root** 下
- `calib_sample_ik.py` 把它们放在 `/observations/` 下

因此如果后处理脚本要统一读 HDF5，建议先固定一个版本作为标准。

---

## 如何在当前主机上继续用 HDF5 采集

## 1. 启动机器人和相机相关 ROS 节点

项目里已有启动脚本：

```bash
./start_sample.sh
```

这个脚本会启动：

- `follow1` 机械臂节点
- `master1` 机械臂节点
- 相机 launch

如果你的采集脚本依赖别的 topic，也要先确认对应节点已经启动。

---

## 2. 选择一个 HDF5 脚本

例如：

- 双相机：`follow1/src/arm_control/scripts/sample_initial.py`
- 单相机：`follow1/src/arm_control/scripts/sample_ik.py`
- 三相机：`follow1/src/arm_control/scripts/sample_ik_3_prep.py`
- 标定：`follow1/src/arm_control/scripts/calib_sample_ik.py`

---

## 3. 先修改脚本里的硬编码参数

运行前至少检查这些参数：

- `directory_path`
- `Max_step`
- 订阅的 ROS topic 名称
- 是否需要 `left/right/mid` 相机
- 是否需要 `joint_control` / `joint_information` / `follow1_pos_back`

例如这些路径在仓库里很多还是旧机器路径：

- `/media/dc/...`
- `/home/dc/...`

如果不改，当前主机上大概率会把数据写到不存在的目录，或者直接失败。

---

## 4. 确保输出目录存在

这些脚本通常**不会主动创建完整目录树**，尤其是：

- `directory_path`
- `directory_path/video`

所以建议先手动创建：

```bash
mkdir -p /你的数据目录/video
```

---

## 5. 在工作区环境下运行采集脚本

建议不要直接依赖脚本第一行的 shebang，因为其中很多仍然写着旧环境路径，如：

- `#!/home/dc/anaconda3/envs/dc/bin/python`

更稳妥的方式是：

```bash
cd /home/arxpro/chenzh/ARX_control_master/follow1
source devel/setup.bash
python src/arm_control/scripts/sample_initial.py
```

如果当前 Python 环境里没有 `h5py`、`rospy`、`cv_bridge` 等依赖，需要先切到正确环境。

---

## 运行成功后的输出

通常会生成：

- `episode_0.hdf5`
- `episode_1.hdf5`
- ...

以及视频：

- `video/0video.mp4`
- `video/1video.mp4`
- ...

文件名由脚本通过统计已有 `.hdf5` 文件数自动递增。

---

## 目前的限制和注意事项

### 1. HDF5 不是当前默认格式
当前主线已经切换到 Zarr，因此：

- 新的数据处理脚本可能默认面向 Zarr
- 点云/深度后处理脚本里也更多使用 Zarr

### 2. HDF5 各脚本字段不完全统一
不同脚本之间存在差异：

- 有的带 `action`
- 有的不带 `action`
- 有的带 `left/right`
- 有的只有 `mid`
- 有的把字段放 root
- 有的放 `/observations`

### 3. 大量路径为硬编码
多数 HDF5 脚本里都写死了旧路径，需要先改。

### 4. shebang 多为旧机器环境
脚本头部很多还是：

```python
#!/home/dc/anaconda3/envs/dc/bin/python
```

当前主机不应直接依赖这个解释器路径。

### 5. 当前仓库根目录下没有现成 HDF5 样本
当前我检查到的实际已生成数据是 `.zarr`，没有在当前默认数据目录下看到 `.hdf5` 样本，所以：

- **代码层面可以继续采 HDF5**
- **但当前实际最近落盘的数据格式是 Zarr**

---

## 建议

如果你只是想“继续兼容旧训练代码”，可以保留 HDF5。

如果你想“和当前项目主流程保持一致”，建议继续用 Zarr。

如果你一定要在当前主机上用 HDF5，建议优先从下面两个脚本二选一开始整理：

- `sample_initial.py`：双相机、结构比较直观
- `sample_ik.py`：单相机、最简单

这样后续最容易统一成一个正式的 HDF5 标准版本。

---

## 可进一步做的事

如果后续需要，我可以继续帮你做下面任一项：

1. **把一个 HDF5 脚本改成当前主机可直接运行版本**
2. **统一所有 HDF5 脚本的数据字段结构**
3. **写一个 HDF5 -> Zarr 转换脚本**
4. **写一个 HDF5 数据读取/可视化脚本**

