import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import sys
from convert_audio_to_p3 import encode_audio_to_opus
from convert_p3_to_audio import decode_p3_to_audio

class AudioConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("音频/P3批量转换工具")
        master.geometry("680x600")  # 调整初始窗口大小

        # 初始化变量
        self.mode = tk.StringVar(value="audio_to_p3")
        self.input_files = []
        self.output_dir = tk.StringVar()
        self.output_dir.set(os.path.abspath("output"))
        self.enable_loudnorm = tk.BooleanVar(value=True)
        self.target_lufs = tk.DoubleVar(value=-16.0)

        # 创建UI组件
        self.create_widgets()
        
        # 初始化日志重定向
        self.redirect_output()

    def create_widgets(self):
        # 模式选择
        mode_frame = ttk.LabelFrame(self.master, text="转换模式")
        mode_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Radiobutton(mode_frame, text="音频转P3", variable=self.mode,
                        value="audio_to_p3", command=self.toggle_settings,
                        width=12).grid(row=0, column=0, padx=5)
        ttk.Radiobutton(mode_frame, text="P3转音频", variable=self.mode,
                        value="p3_to_audio", command=self.toggle_settings,
                        width=12).grid(row=0, column=1, padx=5)

        # 响度设置
        self.loudnorm_frame = ttk.Frame(self.master)
        self.loudnorm_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Checkbutton(self.loudnorm_frame, text="启用响度调整", 
                       variable=self.enable_loudnorm, width=15
                       ).grid(row=0, column=0, padx=2)
        ttk.Entry(self.loudnorm_frame, textvariable=self.target_lufs, 
                 width=6).grid(row=0, column=1, padx=2)
        ttk.Label(self.loudnorm_frame, text="LUFS").grid(row=0, column=2, padx=2)

        # 文件选择
        file_frame = ttk.LabelFrame(self.master, text="输入文件")
        file_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        ttk.Button(file_frame, text="选择文件", command=self.select_files,
                  width=12).grid(row=0, column=0, padx=5, pady=2)
        self.file_list = tk.Listbox(file_frame, height=8, width=60)
        self.file_list.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=2)

        # 输出目录
        output_frame = ttk.LabelFrame(self.master, text="输出目录")
        output_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Entry(output_frame, textvariable=self.output_dir, width=60
                 ).grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(output_frame, text="浏览", command=self.select_output_dir,
                  width=8).grid(row=0, column=1, padx=5)

        # 转换按钮
        ttk.Button(self.master, text="开始转换", command=self.start_conversion,
                  width=20).grid(row=4, column=0, padx=10, pady=10)

        # 日志区域
        log_frame = ttk.LabelFrame(self.master, text="日志")
        log_frame.grid(row=5, column=0, padx=10, pady=5, sticky="nsew")
        
        self.log_text = tk.Text(log_frame, height=12, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 配置布局权重
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(2, weight=1)  # 文件列表区域
        self.master.rowconfigure(5, weight=3)  # 日志区域
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(1, weight=1)

    def toggle_settings(self):
        if self.mode.get() == "audio_to_p3":
            self.loudnorm_frame.grid()
        else:
            self.loudnorm_frame.grid_remove()

    def select_files(self):
        file_types = [
            ("音频文件", "*.wav *.mp3 *.ogg *.flac") if self.mode.get() == "audio_to_p3" 
            else ("P3文件", "*.p3")
        ]
        
        files = filedialog.askopenfilenames(filetypes=file_types)
        if files:
            self.input_files = files
            self.file_list.delete(0, tk.END)
            for f in files:
                self.file_list.insert(tk.END, os.path.basename(f))

    def select_output_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir.set(path)

    def redirect_output(self):
        class StdoutRedirector:
            def __init__(self, text_widget):
                self.text_widget = text_widget

            def write(self, message):
                self.text_widget.insert(tk.END, message)
                self.text_widget.see(tk.END)

        sys.stdout = StdoutRedirector(self.log_text)

    def start_conversion(self):
        if not self.input_files:
            messagebox.showwarning("警告", "请先选择输入文件")
            return
        
        os.makedirs(self.output_dir.get(), exist_ok=True)

        if self.mode.get() == "audio_to_p3":
            target_lufs = self.target_lufs.get() if self.enable_loudnorm.get() else None
            thread = threading.Thread(target=self.convert_audio_to_p3, args=(target_lufs,))
        else:
            thread = threading.Thread(target=self.convert_p3_to_audio)
        
        thread.start()

    def convert_audio_to_p3(self, target_lufs):
        for input_path in self.input_files:
            try:
                filename = os.path.basename(input_path)
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(self.output_dir.get(), f"{base_name}.p3")
                
                print(f"正在转换: {filename}")
                encode_audio_to_opus(input_path, output_path, target_lufs)
                print(f"转换成功: {filename}\n")
            except Exception as e:
                print(f"转换失败: {str(e)}\n")

    def convert_p3_to_audio(self):
        for input_path in self.input_files:
            try:
                filename = os.path.basename(input_path)
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(self.output_dir.get(), f"{base_name}.wav")
                
                print(f"正在转换: {filename}")
                decode_p3_to_audio(input_path, output_path)
                print(f"转换成功: {filename}\n")
            except Exception as e:
                print(f"转换失败: {str(e)}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioConverterApp(root)
    root.mainloop()