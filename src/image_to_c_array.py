import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import os
import tempfile
from LVGLImage import LVGLImage, ColorFormat, CompressMethod

class ImageConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LVGL图片转换工具")
        
        # 初始化变量
        self.selected_files = []
        self.resolution = tk.StringVar(value="128x128")
        self.output_dir = "output"
        
        # 创建界面组件
        self.create_widgets()
        
    def create_widgets(self):
        # 文件选择按钮
        self.select_button = ttk.Button(self.root, text="选择图片文件", command=self.select_files)
        self.select_button.pack(pady=10)
        
        # 分辨率选择框架
        res_frame = ttk.LabelFrame(self.root, text="选择分辨率")
        res_frame.pack(pady=5, padx=10, fill="x")
        
        resolutions = [
            ("128x128", "128x128"),
            ("64x64", "64x64"),
            ("32x32", "32x32")  # 新增32x32选项
        ]
        
        for text, value in resolutions:
            ttk.Radiobutton(res_frame, 
                          text=text,
                          variable=self.resolution,
                          value=value).pack(side=tk.LEFT, padx=5)
        
        # 转换按钮
        self.convert_button = ttk.Button(self.root, text="开始转换", command=self.convert_images)
        self.convert_button.pack(pady=10)
        
        # 日志输出框
        self.log = tk.Text(self.root, height=10, width=60, state=tk.DISABLED)
        self.log.pack(pady=10, padx=10)
        
        # 进度条
        self.progress = ttk.Progressbar(self.root, mode="determinate")
        
    def select_files(self):
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if files:
            self.selected_files = files
            self.log_write(f"已选择 {len(files)} 个文件\n")
        
    def convert_images(self):
        if not self.selected_files:
            messagebox.showwarning("警告", "请先选择图片文件！")
            return
        
        # 初始化进度条
        self.progress.pack(pady=5)
        self.progress["maximum"] = len(self.selected_files)
        self.progress["value"] = 0
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 解析分辨率
        width, height = map(int, self.resolution.get().split('x'))
        
        success_count = 0
        for idx, file_path in enumerate(self.selected_files):
            try:
                # 更新进度
                self.progress["value"] = idx + 1
                self.root.update_idletasks()
                
                # 处理每个文件
                with Image.open(file_path) as img:
                    # 调整图片大小
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                    
                    # 处理透明通道
                    has_alpha = img.mode in ('RGBA', 'LA')
                    if has_alpha:
                        img = img.convert('RGBA')
                        cf = ColorFormat.RGB565A8
                    else:
                        img = img.convert('RGB')
                        cf = ColorFormat.RGB565
                    
                    # 保存调整后的图片
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    output_image_name = f"{base_name}_{width}x{height}.png"
                    output_image_path = os.path.join(self.output_dir, output_image_name)
                    img.save(output_image_path, 'PNG')
                    self.log_write(f"已保存调整后的图片: {output_image_name}\n")
                    
                    # 创建临时文件
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                        temp_path = tmpfile.name
                        img.save(temp_path, 'PNG')
                    
                    # 转换为LVGL C数组
                    lvgl_img = LVGLImage().from_png(temp_path, cf=cf)
                    
                    # 生成C数组文件名
                    output_c_path = os.path.join(self.output_dir, f"{base_name}.c")
                    
                    # 保存C数组文件
                    lvgl_img.to_c_array(output_c_path)
                    
                    # 记录日志
                    self.log_write(f"成功转换：{base_name}.c\n")
                    success_count += 1
                    
                    # 清理临时文件
                    os.unlink(temp_path)
                    
            except Exception as e:
                self.log_write(f"错误处理文件 {os.path.basename(file_path)}: {str(e)}\n")
        
        # 完成处理
        self.progress.pack_forget()
        messagebox.showinfo("完成", f"成功转换 {success_count}/{len(self.selected_files)} 个文件")
        self.selected_files = []
        
    def log_write(self, message):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, message)
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageConverterApp(root)
    root.geometry("650x450")
    root.mainloop()