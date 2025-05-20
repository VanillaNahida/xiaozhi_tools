import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import opuslib
import struct
import numpy as np
import sounddevice as sd
import os


def play_p3_file(input_file, stop_event=None, pause_event=None):
    """
    播放p3格式的音频文件
    p3格式: [1字节类型, 1字节保留, 2字节长度, Opus数据]
    """
    # 初始化Opus解码器
    sample_rate = 16000  # 采样率固定为16000Hz
    channels = 1  # 单声道
    decoder = opuslib.Decoder(sample_rate, channels)
    
    # 帧大小 (60ms)
    frame_size = int(sample_rate * 60 / 1000)
    
    # 打开音频流
    stream = sd.OutputStream(
        samplerate=sample_rate,
        channels=channels,
        dtype='int16'
    )
    stream.start()
    
    try:
        with open(input_file, 'rb') as f:
            print(f"正在播放: {input_file}")
            
            while True:
                if stop_event and stop_event.is_set():
                    break

                if pause_event and pause_event.is_set():
                    time.sleep(0.1)
                    continue

                # 读取头部 (4字节)
                header = f.read(4)
                if not header or len(header) < 4:
                    break
                
                # 解析头部
                packet_type, reserved, data_len = struct.unpack('>BBH', header)
                
                # 读取Opus数据
                opus_data = f.read(data_len)
                if not opus_data or len(opus_data) < data_len:
                    break
                
                # 解码Opus数据
                pcm_data = decoder.decode(opus_data, frame_size)
                
                # 将字节转换为numpy数组
                audio_array = np.frombuffer(pcm_data, dtype=np.int16)
                
                # 播放音频
                stream.write(audio_array)
                
                # 等待一帧的时间
                time.sleep(60 / 1000)  # 60ms
            
            # 播放结束后添加0.5秒静音，避免破音
            silence = np.zeros(int(sample_rate / 2), dtype=np.int16)
            stream.write(silence)
            time.sleep(0.5)  # 等待1秒
                
    except KeyboardInterrupt:
        print("\n播放已停止")
    finally:
        stream.stop()
        stream.close()
        print("播放完成")


class P3PlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("P3 文件简易播放器")
        self.root.geometry("680x600")  # 调整窗口大小

        # 初始化变量
        self.playlist = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.loop_playback = tk.BooleanVar(value=False)  # 循环播放复选框的状态
        self.play_thread = None  # 当前播放线程
        self.play_lock = threading.Lock()  # 线程锁，确保播放逻辑的线程安全

        # 创建UI组件
        self.create_widgets()

    def create_widgets(self):
        # 播放列表
        file_frame = ttk.LabelFrame(self.root, text="播放列表")
        file_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        # 文件操作按钮
        ttk.Button(file_frame, text="添加文件", command=self.add_file,
                  width=12).grid(row=0, column=0, padx=5, pady=2)
        ttk.Button(file_frame, text="移除选中", command=self.remove_selected,
                  width=12).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="清空列表", command=self.clear_files,
                  width=12).grid(row=0, column=2, padx=5, pady=2)

        # 文件列表（使用Treeview）
        self.tree = ttk.Treeview(file_frame, columns=("selected", "filename"), 
                               show="headings", height=8)
        self.tree.heading("selected", text="选中", anchor=tk.W)
        self.tree.heading("filename", text="文件名", anchor=tk.W)
        self.tree.column("selected", width=60, anchor=tk.W)
        self.tree.column("filename", width=600, anchor=tk.W)
        self.tree.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=2)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)

        # 控制按钮
        control_frame = ttk.LabelFrame(self.root, text="控制")
        control_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        ttk.Button(control_frame, text="播放", command=self.play,
                  width=12).grid(row=0, column=0, padx=5, pady=2)
        ttk.Button(control_frame, text="暂停", command=self.pause,
                  width=12).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(control_frame, text="停止", command=self.stop,
                  width=12).grid(row=0, column=2, padx=5, pady=2)

        # 循环播放复选框
        ttk.Checkbutton(control_frame, text="循环播放", variable=self.loop_playback,
                      width=12).grid(row=0, column=3, padx=5, pady=2)

        # 状态标签
        self.status_label = ttk.Label(self.root, text="未在播放", foreground="blue")
        self.status_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        # 配置布局权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(1, weight=1)

    def on_tree_click(self, event):
        """处理复选框点击事件"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            col = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            if col == "#1":  # 点击的是选中列
                current_val = self.tree.item(item, "values")[0]
                new_val = "[√]" if current_val == "[ ]" else "[ ]"
                self.tree.item(item, values=(new_val, self.tree.item(item, "values")[1]))

    def add_file(self):
        files = filedialog.askopenfilenames(filetypes=[("P3 文件", "*.p3")])
        if files:
            for file in files:
                self.playlist.append(file)
                self.tree.insert("", tk.END, values=("[ ]", os.path.basename(file)), tags=(file,))

    def remove_selected(self):
        """移除选中的文件"""
        to_remove = []
        for item in self.tree.get_children():
            if self.tree.item(item, "values")[0] == "[√]":
                to_remove.append(item)
        
        for item in reversed(to_remove):
            file_path = self.tree.item(item, "tags")[0]
            if file_path == self.playlist[self.current_index]:  # 检查是否正在播放的文件
                self.stop()  # 如果是，则停止播放
            elif self.playlist.index(file_path) < self.current_index:  # 如果文件在当前播放文件之前
                self.current_index -= 1  # 调整 current_index
            self.tree.delete(item)
            self.playlist.remove(file_path)

    def clear_files(self):
        """清空所有文件"""
        if self.is_playing or self.is_paused:
            self.stop()  # 如果正在播放，则停止播放
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.playlist.clear()
        self.current_index = 0  # 重置 current_index

    def update_status(self, status_text, color="blue"):
        """更新状态标签的内容"""
        self.status_label.config(text=status_text, foreground=color)

    def play(self):
        if not self.playlist:
            messagebox.showwarning("警告", "播放列表为空！")
            return

        # 使用线程锁确保播放逻辑的线程安全
        with self.play_lock:
            # 如果正在播放，强制停止当前播放
            if self.is_playing:
                self.stop_event.set()  # 设置停止事件
                if self.play_thread:
                    self.play_thread.join(timeout=0.1)  # 等待播放线程结束
                self.play_thread = None

            # 检查是否有选中的文件
            selected_items = self.tree.selection()
            if selected_items:
                self.current_index = self.tree.index(selected_items[0])  # 更新为选中文件的索引

            # 检查 current_index 是否有效
            if self.current_index >= len(self.playlist):
                self.current_index = 0  # 如果无效，则重置为 0

            # 更新状态标签
            self.update_status(f"正在播放：{os.path.basename(self.playlist[self.current_index])}", "green")

            # 启动新的播放线程
            self.is_playing = True
            self.stop_event.clear()
            self.pause_event.clear()
            self.play_thread = threading.Thread(target=self.play_audio, daemon=True)
            self.play_thread.start()

    def play_audio(self):
        while True:
            if self.stop_event.is_set():
                break

            if self.pause_event.is_set():
                time.sleep(0.1)
                continue

            # 检查当前索引是否有效
            if self.current_index >= len(self.playlist):
                if self.loop_playback.get():  # 如果勾选了循环播放
                    self.current_index = 0  # 回到第一首
                else:
                    break  # 否则停止播放

            file = self.playlist[self.current_index]
            if file not in self.playlist:  # 检查文件是否仍在播放列表中
                break  # 如果文件被移除，则停止播放

            self.tree.selection_clear()
            self.tree.selection_set(self.tree.get_children()[self.current_index])
            self.tree.focus(self.tree.get_children()[self.current_index])
            play_p3_file(file, self.stop_event, self.pause_event)

            if self.stop_event.is_set():
                break

            if not self.loop_playback.get():  # 如果没有勾选循环播放
                break  # 播放完当前文件后停止

            self.current_index += 1
            if self.current_index >= len(self.playlist):
                if self.loop_playback.get():  # 如果勾选了循环播放
                    self.current_index = 0  # 回到第一首

        self.is_playing = False
        self.is_paused = False
        self.update_status("播放已停止", "red")

    def pause(self):
        if self.is_playing:
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.pause_event.set()
                self.update_status("播放已暂停", "orange")
            else:
                self.pause_event.clear()
                self.update_status(f"正在播放：{os.path.basename(self.playlist[self.current_index])}", "green")

    def stop(self):
        if self.is_playing or self.is_paused:
            self.is_playing = False
            self.is_paused = False
            self.stop_event.set()
            self.pause_event.clear()
            self.update_status("播放已停止", "red")


if __name__ == "__main__":
    root = tk.Tk()
    app = P3PlayerApp(root)
    root.mainloop()