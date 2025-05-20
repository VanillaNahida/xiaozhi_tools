# 说明
*以下内容由DeepSeek R1生成，仅供参考。请以实际为准！*
# 多功能工具集

本目录包含多个实用工具，涵盖音频处理、图像转换等功能：

## 1. 音频转换工具集

### 1.1 基础格式转换 (convert_audio_to_p3.py)
将普通音频文件转换为P3格式（4字节header + Opus数据包的流式结构）并进行响度标准化

#### 使用方法
```bash
python convert_audio_to_p3.py <输入音频文件> <输出P3文件> [-l LUFS] [-d]
```

### 1.2 音频转回工具 (convert_p3_to_audio.py)
将P3格式转换回普通音频文件

#### 使用方法
```bash
python convert_p3_to_audio.py <输入P3文件> <输出音频文件>
```

### 1.3 批量转换工具 (p3_convertor.py)
带图形界面的批量转换工具，支持双向转换

#### 特性
- 支持批量音频 ↔ P3 格式互转
- 实时转换进度显示
- 可调节响度标准化参数

#### 使用方法
```bash
python p3_convertor.py
```

## 2. 音频播放工具集

### 2.1 命令行播放器 (play_p3.py)
播放P3格式的音频文件

#### 使用方法
```bash
python play_p3.py <P3文件路径>
```

### 2.2 图形界面播放器 (p3_gui_player.py)
带播放列表的GUI播放器

#### 特性
- 支持播放列表管理
- 循环播放功能
- 实时状态显示

#### 使用方法
```bash
python p3_gui_player.py
```

## 3. 图像转换工具 (image_to_c_array.py)
将图片转换为LVGL可用的C语言数组格式

#### 特性
- 支持多种分辨率预设（128x128/64x64/32x32）
- 批量转换功能
- 转换进度显示

#### 使用方法
```bash
python image_to_c_array.py
```

## 依赖安装

使用前请安装所需库：
```bash
pip install -r requirements.txt
```

## 文件格式说明

### P3音频格式
- 采样率：16000Hz
- 单声道
- 帧结构：[1字节类型][1字节保留][2字节长度][Opus数据]
- 每帧时长：60ms

### LVGL图像格式
- 输出为C语言头文件
- 包含像素数据数组
- 自动生成尺寸定义
```

        