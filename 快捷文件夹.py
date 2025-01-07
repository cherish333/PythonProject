
import tkinter as tk
from tkinter import filedialog
import json
import os
import subprocess
from tkinter import ttk
# 默认路径配置
DEFAULT_PATHS = {
    # 移除默认路径
}
class DarkScrollbar(tk.Canvas):
    """自定义深色滚动条"""
    def __init__(self, parent, **kwargs):
        self.command = kwargs.pop('command', None)  # 保存command参数
        bg = kwargs.pop('bg', '#2b2b2b')
        width = kwargs.pop('width', 10)
        super().__init__(parent, width=width, bg=bg, highlightthickness=0, **kwargs)
        
        # 创建滚动条
        self._offset = 0
        self._scroll_bar = None
        self._create_scroll_bar()
        
        # 绑定事件
        self.bind('<Configure>', self._on_configure)
        self.bind('<Button-1>', self._on_click)
        self.bind('<B1-Motion>', self._on_drag)
    
    def _create_scroll_bar(self):
        """创建滚动条"""
        if self._scroll_bar:
            self.delete(self._scroll_bar)
        height = self.winfo_height() - 2*self._offset
        if height > 0:
            self._scroll_bar = self.create_rectangle(
                2, self._offset,
                self.winfo_width()-2, height,
                fill='#4c5052',  # 滚动条颜色
                outline='#4c5052',  # 边框颜色
                tags=('scrollbar',),
                width=0
            )
    
    def _on_configure(self, event):
        """处理大小改变事件"""
        self._create_scroll_bar()
    
    def _on_click(self, event):
        """处理点击事件"""
        if self.command:
            # 计算相对位置并调用command
            fraction = event.y / self.winfo_height()
            self.command('moveto', fraction)
    
    def _on_drag(self, event):
        """处理拖动事件"""
        if self.command:
            # 计算相对位置并调用command
            fraction = event.y / self.winfo_height()
            self.command('moveto', fraction)
    
    def set(self, first, last):
        """设置滚动条位置"""
        first = float(first)
        last = float(last)
        height = self.winfo_height()
        top = height * first
        bottom = height * last
        self._offset = top
        self._create_scroll_bar()
    def configure(self, **kwargs):
        """配置滚动条"""
        if 'command' in kwargs:
            self.command = kwargs.pop('command')
        super().configure(**kwargs)
class FolderAccessTool:
    # 定义字体常量
    FONT_FAMILY = "Microsoft YaHei"
    FONT_NORMAL = ("Microsoft YaHei", 9)
    FONT_BOLD = ("Microsoft YaHei", 11, "bold")
    FONT_TITLE = ("Microsoft YaHei", 10)
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Folder Quick Access")
        self.root.geometry("400x500")
        self.root.configure(bg="#2b2b2b")
        
        # 设置窗口图标 - 修改路径格式
        try:
            icon_path = "D:\\python\\IG.ico"  # 使用双反斜杠
            # 或者使用正斜杠
            # icon_path = "D:/python/IG.ico"
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icon loading error: {e}")  # 添加错误输出以便调试
        
        # 修改窗口样式设置
        self.root.wm_attributes('-topmost', True)  # 保持窗口在最前
        
        # 设置窗口样式但保留最小化按钮
        if os.name == 'nt':  # Windows系统
            try:
                from ctypes import windll
                GWL_STYLE = -16
                WS_MINIMIZEBOX = 0x00020000
                # 获取当前窗口样式
                style = windll.user32.GetWindowLongW(self.root.winfo_id(), GWL_STYLE)
                # 添加最小化按钮样式
                style |= WS_MINIMIZEBOX
                # 应用新样式
                windll.user32.SetWindowLongW(self.root.winfo_id(), GWL_STYLE, style)
            except:
                pass  # 如果出现任何错误，忽略它
        
        self.add_dialog = None  # 用于存储添加路径的对话框
        
        # 居中窗口
        self._center_window()
        
        # 移除自定义标题栏的创建
        # self._create_title_bar()
        
        # 创建主框架
        self.main_frame = tk.Frame(self.root, bg="#2b2b2b")
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # 创建按钮显示区域的容器框架
        buttons_container = tk.Frame(self.main_frame, bg="#2b2b2b")
        buttons_container.pack(fill="both", expand=True, pady=(0, 10))
        
        # 创建画布和滚动条
        self.canvas = tk.Canvas(buttons_container, bg="#2b2b2b", highlightthickness=0)
        scrollbar = DarkScrollbar(buttons_container, width=10)
        scrollbar.configure(command=self.canvas.yview)
        
        # 创建按钮显示区域
        self.buttons_frame = tk.Frame(self.canvas, bg="#2b2b2b")
        
        # 配置画布
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # 打包滚动条和画布
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # 在画布上创建窗口
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.buttons_frame, anchor="nw")
        
        # 添加复制路径选项的状态变量
        self.copy_path_enabled = tk.BooleanVar(value=False)
        
        # 创建工具栏（放在下方）
        self._create_toolbar()
        
        # 添加窗口大小调整区域
        self._create_resize_area()
        
        # 在类初始化时定义配置文件路径
        self.config_dir = os.path.join(os.getenv('APPDATA'), 'FolderQuickAccess')
        self.config_file = os.path.join(self.config_dir, 'paths.json')
        
        # 确保配置目录存在
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        # 加载保存的路径
        self.paths_data = self._load_paths()
        
        # 移除默认路径的处理
        # if not self.paths_data:
        #     self.paths_data = DEFAULT_PATHS.copy()
        #     self._save_paths()
            
        self._create_path_buttons()
        
        # 绑定事件
        self.buttons_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # 绑定整个窗口的拖动
        self._bind_window_move(self.root)
        
    def _center_window(self):
        """将窗口居中"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 500) // 2
        self.root.geometry(f"400x500+{x}+{y}")
        
    def _bind_window_move(self, widget):
        """绑定窗口拖动事件到指定widget"""
        def start_move(event):
            self.root.x = event.x
            self.root.y = event.y
            
        def stop_move(event):
            self.root.x = None
            self.root.y = None
            
        def do_move(event):
            deltax = event.x - self.root.x
            deltay = event.y - self.root.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")
            
        widget.bind("<Button-1>", start_move)
        widget.bind("<ButtonRelease-1>", stop_move)
        widget.bind("<B1-Motion>", do_move)
    def _create_toolbar(self):
        """创建工具栏"""
        # 创建一个框架来容纳按钮，放在底部
        toolbar = tk.Frame(self.main_frame, bg="#2b2b2b", height=40)
        toolbar.pack(side="bottom", fill="x", pady=10)
        toolbar.pack_propagate(False)
        
        # 创建一个内部框架来居中放置按钮和复选框
        button_container = tk.Frame(toolbar, bg="#2b2b2b")
        button_container.pack(expand=True, pady=5)
        
        # 添加路径按钮
        add_btn = tk.Button(
            button_container,
            text="Add Path",
            command=self._show_add_dialog,
            bg="#4c5052",
            fg="white",
            activebackground="#5c6062",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            width=10,
            height=1,
            font=self.FONT_NORMAL
        )
        add_btn.pack(side="left", padx=5)
        
        # 添加复选框
        copy_checkbox = tk.Checkbutton(
            button_container,
            text="Copy Path",
            variable=self.copy_path_enabled,
            bg="#2b2b2b",
            fg="white",
            selectcolor="#2b2b2b",
            activebackground="#2b2b2b",
            activeforeground="white",
            font=self.FONT_NORMAL
        )
        copy_checkbox.pack(side="left", padx=10)
        
        # 添加按钮悬停效果
        def on_enter(e):
            e.widget['background'] = '#5c6062'
        def on_leave(e):
            e.widget['background'] = '#4c5052'
        add_btn.bind("<Enter>", on_enter)
        add_btn.bind("<Leave>", on_leave)
    def _show_add_dialog(self):
        """显示添加路径对话框"""
        if self.add_dialog:
            return
            
        self.add_dialog = tk.Toplevel(self.root)
        self.add_dialog.title("Add Path")
        self.add_dialog.geometry("300x200")
        self.add_dialog.configure(bg="#2b2b2b")
        self.add_dialog.transient(self.root)
        
        # 对话框内容框架
        dialog_frame = tk.Frame(self.add_dialog, bg="#2b2b2b")
        dialog_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # 路径输入框
        path_label = tk.Label(
            dialog_frame,
            text="Path:",
            bg="#2b2b2b",
            fg="white",
            font=self.FONT_TITLE
        )
        path_label.pack(anchor="w")
        
        path_entry = tk.Entry(
            dialog_frame,
            bg="#1e1e1e",
            fg="white",
            insertbackground="white",
            relief="flat",
            highlightbackground="#1e1e1e",
            highlightcolor="#4c5052",
            highlightthickness=1
        )
        path_entry.pack(fill="x", pady=(0, 10))
        
        # 按钮名称输入框
        name_label = tk.Label(
            dialog_frame,
            text="Button Name:",
            bg="#2b2b2b",
            fg="white",
            font=self.FONT_TITLE
        )
        name_label.pack(anchor="w")
        
        name_entry = tk.Entry(
            dialog_frame,
            bg="#1e1e1e",
            fg="white",
            insertbackground="white",
            relief="flat",
            highlightbackground="#1e1e1e",
            highlightcolor="#4c5052",
            highlightthickness=1
        )
        name_entry.pack(fill="x", pady=(0, 10))
        
        # 按钮框架
        btn_frame = tk.Frame(dialog_frame, bg="#2b2b2b")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        # 浏览按钮
        browse_btn = tk.Button(
            btn_frame,
            text="Browse",
            command=lambda: self._browse_path(path_entry),
            bg="#4c5052",
            fg="white",
            activebackground="#5c6062",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            font=self.FONT_NORMAL
        )
        browse_btn.pack(side="left", padx=5)
        
        # 确认按钮
        confirm_btn = tk.Button(
            btn_frame,
            text="Add",
            command=lambda: self._confirm_add(path_entry.get(), name_entry.get()),
            bg="#4c5052",
            fg="white",
            activebackground="#5c6062",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            font=self.FONT_NORMAL
        )
        confirm_btn.pack(side="left", padx=5)
        
        def on_dialog_close():
            self.add_dialog.destroy()
            self.add_dialog = None
            
        self.add_dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
        self.add_dialog.grab_set()
    def _create_path_buttons(self):
        """创建路径按钮"""
        # 清除现有按钮
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        
        # 创建网格布局框架
        grid_frame = tk.Frame(self.buttons_frame, bg="#2b2b2b")
        grid_frame.pack(expand=True, fill="both")
        
        # 计算每行显示的按钮数量
        buttons_per_row = 2
        
        # 修改按钮点击事件
        def create_button_command(path):
            def command():
                # 根据复选框状态决定行为
                if self.copy_path_enabled.get():
                    # 只复制路径
                    self.root.clipboard_clear()
                    self.root.clipboard_append(path)
                    self._show_message("Path copied!")  # 添加复制路径的提示
                else:
                    # 只打开文件夹
                    self._open_path(path)
            return command
        
        # 创建新按钮
        for index, (name, path) in enumerate(self.paths_data.items()):
            row = index // buttons_per_row
            col = index % buttons_per_row
            
            # 创建按钮框架
            button_frame = tk.Frame(grid_frame, bg="#2b2b2b")
            button_frame.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
            
            # 访问按钮
            btn = tk.Button(
                button_frame,
                text=name,
                command=create_button_command(path),  # 使用新的命令创建函数
                bg="#4c5052",
                fg="white",
                activebackground="#5c6062",
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                width=20,
                height=2,
                font=self.FONT_BOLD
            )
            btn.pack(side="left", padx=5, expand=True)
            
            # 创建右键菜单
            menu = tk.Menu(btn, tearoff=0, bg="#2b2b2b", fg="white", 
                          activebackground="#E81123", activeforeground="white",
                          font=self.FONT_NORMAL)
            menu.add_command(
                label="Delete",
                command=lambda n=name: self._delete_path(n),
                font=self.FONT_NORMAL
            )
            
            # 绑定右键事件
            def show_menu(event, m=menu):
                m.post(event.x_root, event.y_root)
                
            btn.bind("<Button-3>", show_menu)  # Windows右键
            btn.bind("<Control-Button-1>", show_menu)  # Mac右键替代
        
        # 配置网格列的权重，使其均匀分布
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
    def _open_path(self, path):
        """打开文件夹"""
        if os.path.exists(path):
            subprocess.run(['explorer', path])
            
    def _delete_path(self, name):
        """删除路径"""
        if name in self.paths_data:
            # 显示确认对话框
            confirm_window = tk.Toplevel(self.root)
            confirm_window.overrideredirect(True)
            confirm_window.configure(bg="#1e1e1e")
            confirm_window.attributes('-topmost', True)
            
            # 设置窗口位置
            window_width = 300
            window_height = 100
            x = self.root.winfo_x() + (self.root.winfo_width() - window_width) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - window_height) // 2
            confirm_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # 创建带边框的框架
            frame = tk.Frame(
                confirm_window,
                bg="#1e1e1e",
                highlightbackground="#4c5052",
                highlightthickness=1
            )
            frame.pack(fill="both", expand=True, padx=2, pady=2)
            
            # 添加确认消息
            msg_label = tk.Label(
                frame,
                text=f"Delete '{name}'?",
                bg="#1e1e1e",
                fg="white",
                font=self.FONT_TITLE
            )
            msg_label.pack(pady=(15, 10))
            
            # 按钮框架
            btn_frame = tk.Frame(frame, bg="#1e1e1e")
            btn_frame.pack(pady=(0, 10))
            
            # 确认按钮
            def confirm():
                del self.paths_data[name]
                self._save_paths()
                self._create_path_buttons()
                confirm_window.destroy()
                self._show_message("Path deleted!")
                
            confirm_btn = tk.Button(
                btn_frame,
                text="Delete",
                command=confirm,
                bg="#E81123",
                fg="white",
                activebackground="#FF1A1A",
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                width=8,
                font=self.FONT_NORMAL
            )
            confirm_btn.pack(side="left", padx=5)
            
            # 取消按钮
            cancel_btn = tk.Button(
                btn_frame,
                text="Cancel",
                command=confirm_window.destroy,
                bg="#4c5052",
                fg="white",
                activebackground="#5c6062",
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                width=8,
                font=self.FONT_NORMAL
            )
            cancel_btn.pack(side="left", padx=5)
            
    def _load_paths(self):
        """加载保存的路径"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    paths = json.load(f)
                    return paths if paths else {}
            return {}
        except:
            return {}
            
    def _save_paths(self):
        """保存路径"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.paths_data, f)
        except Exception as e:
            print(f"Error saving paths: {e}")
            
    def _show_message(self, message):
        """显示消息"""
        msg_window = tk.Toplevel(self.root)
        msg_window.overrideredirect(True)
        msg_window.configure(bg="#1e1e1e")
        msg_window.attributes('-topmost', True)
        
        # 设置消息框位置
        window_width = 200
        window_height = 60
        x = self.root.winfo_x() + (self.root.winfo_width() - window_width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - window_height) // 2
        msg_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建带边框的框架
        frame = tk.Frame(
            msg_window,
            bg="#1e1e1e",
            highlightbackground="#4c5052",
            highlightthickness=1
        )
        frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # 添加消息
        msg_label = tk.Label(
            frame,
            text=message,
            bg="#1e1e1e",
            fg="white",
            font=self.FONT_TITLE
        )
        msg_label.pack(pady=15)
        
        # 1秒后自动关闭
        msg_window.after(1000, msg_window.destroy)
        
    def _browse_path(self, entry):
        """浏览文件夹"""
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)
    def _confirm_add(self, path, name):
        """确认添加路径"""
        if path and name:
            self.paths_data[name] = path
            self._save_paths()
            self._create_path_buttons()
            self.add_dialog.destroy()
            self.add_dialog = None
            self._show_message("Path added successfully!")
        
    def _on_frame_configure(self, event=None):
        """更新画布的滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    def _on_canvas_configure(self, event):
        """当画布大小改变时，调整内部框架的宽度"""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        if self.canvas.winfo_height() < self.buttons_frame.winfo_height():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    def _create_resize_area(self):
        """创建窗口大小调整区域"""
        resize_frame = tk.Frame(self.root, bg="#1e1e1e", height=4, cursor="sb_v_double_arrow")
        resize_frame.pack(side="bottom", fill="x")
        
        def start_resize(event):
            self.root.start_y = event.y_root
            self.root.start_height = self.root.winfo_height()
        
        def do_resize(event):
            height_diff = event.y_root - self.root.start_y
            new_height = self.root.start_height + height_diff
            # 限制最小和最大高度
            new_height = max(300, min(new_height, self.root.winfo_screenheight() - 100))
            self.root.geometry(f"400x{new_height}")
        
        resize_frame.bind("<Button-1>", start_resize)
        resize_frame.bind("<B1-Motion>", do_resize)
        
        # 添加视觉反馈
        def on_enter(event):
            resize_frame.configure(bg="#4c5052")
        
        def on_leave(event):
            resize_frame.configure(bg="#1e1e1e")
        
        resize_frame.bind("<Enter>", on_enter)
        resize_frame.bind("<Leave>", on_leave)
    def run(self):
        """运行程序"""
        self.root.mainloop()
if __name__ == "__main__":
    app = FolderAccessTool()
    app.run()
