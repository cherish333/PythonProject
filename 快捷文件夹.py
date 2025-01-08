import tkinter as tk
from tkinter import filedialog
import json
import os
import subprocess
from tkinterdnd2 import *
import winshell
from win32com.client import Dispatch
import re
from PIL import Image, ImageTk
import time
# 默认路径配置:
DEFAULT_PATHS = {
    # 移除默认路径
}
class DarkScrollbar(tk.Canvas):
    """自定义深色滚动条"""
    def __init__(self, parent, **kwargs):
        self.command = kwargs.pop('command', None)
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
                fill='#4c5052',
                outline='#4c5052',
                tags=('scrollbar',),
                width=0
            )
    
    def _on_configure(self, event):
        """处理大小改变事件"""
        self._create_scroll_bar()
    
    def _on_click(self, event):
        """处理点击事件"""
        if self.command:
            fraction = event.y / self.winfo_height()
            self.command('moveto', fraction)
    def _on_drag(self, event):
        """处理拖动事件"""
        if self.command:
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
    # 添加支持的文件格式
    SUPPORTED_FORMATS = {
        "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
        "视频": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
        "文档": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"]
    }
    
    # 保持原有的字体设置
    FONT_FAMILY = "Microsoft YaHei"
    FONT_NORMAL = ("Microsoft YaHei", 9)
    FONT_BOLD = ("Microsoft YaHei", 11, "bold")
    FONT_TITLE = ("Microsoft YaHei", 10)
    # 添加特殊软件路径搜索配置
    SPECIAL_SOFTWARE_PATHS = {
        "Logitech G HUB": {
            "name": "Logitech G HUB",
            "possible_paths": [
                "C:\\Program Files\\LGHUB\\lghub.exe",
                "C:\\Program Files (x86)\\LGHUB\\lghub.exe",
                os.path.expandvars("%LOCALAPPDATA%\\LGHUB\\lghub.exe")
            ],
            "icon": "🎮"
        },
        "FastStone Capture": {
            "name": "FastStone Capture",
            "possible_paths": [
                "C:\\Program Files\\FastStone Capture\\FSCapture.exe",
                "C:\\Program Files (x86)\\FastStone Capture\\FSCapture.exe"
            ],
            "icon": "📸"
        },
        "Steam Games": {
            "name": "Steam Games",
            "possible_paths": [
                "C:\\Program Files (x86)\\Steam\\steamapps\\common",
                "C:\\Program Files\\Steam\\steamapps\\common",
                "D:\\Steam\\steamapps\\common",
                "E:\\Steam\\steamapps\\common"
            ],
            "icon": "🎮"
        },
        "Epic Games": {
            "name": "Epic Games",
            "possible_paths": [
                "C:\\Program Files\\Epic Games",
                "C:\\Program Files (x86)\\Epic Games",
                "D:\\Epic Games",
                "E:\\Epic Games"
            ],
            "icon": "🎮"
        }
    },
    # 添加图片预览窗口的配置
    IMAGE_PREVIEW_SIZE = (200, 200)  # 预览窗口大小
    
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("Folder Quick Access")
        self.root.geometry("400x500")
        self.root.configure(bg="#2b2b2b")
        
        # 设置窗口图标
        try:
            icon_path = "D:\\python\\IG.ico"
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icon loading error: {e}")
        
        # 修改窗口样式设置
        if os.name == 'nt':  # Windows系统
            try:
                from ctypes import windll
                GWL_STYLE = -16
                WS_MINIMIZEBOX = 0x00020000
                style = windll.user32.GetWindowLongW(self.root.winfo_id(), GWL_STYLE)
                style |= WS_MINIMIZEBOX
                windll.user32.SetWindowLongW(self.root.winfo_id(), GWL_STYLE, style)
            except:
                pass
        
        self.add_dialog = None  # 用于存储添加路径的对话框
        
        # 居中窗口
        self._center_window()
        
        # 移除自定义标题栏的创建
        # self._create_title_bar()
        
        # 创建主框架
        self.main_frame = tk.Frame(self.root, bg="#2b2b2b")
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # 启用拖放功能
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self._on_drop)
        
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
        
        # 在原有的初始化代码后添加
        self.preview_window = None
        
        # 在原有的初始化代码后添加
        self.hot_corner_active = False
        self.hot_corner_size = 5  # 热区大小（像素）
        self.check_interval = 100  # 检查间隔（毫秒）
        
        # 创建热区检测器
        self._create_hot_corner_detector()
        
        # 绑定最小化事件
        self.root.bind("<Unmap>", self._on_minimize)
        self.root.bind("<Map>", self._on_restore)
        
    def _center_window(self):
        """将窗口位置调整到屏幕左上角"""
        # 窗口尺寸
        window_width = 400
        window_height = 500
        
        # 设置位置：靠近左上角，但留出一点边距
        x = 20  # 距离左边缘20像素
        y = 20  # 距离上边缘20像素
        
        # 设置窗口位置和大小
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 设置窗口最小尺寸
        self.root.minsize(400, 300)
    def _bind_window_move(self, widget):
        """绑定窗口拖动事件到指定widget"""
        def start_move(event):
            # 如果点击的是按钮，不启动窗口移动
            if isinstance(event.widget, tk.Button):
                return
            self.root.x = event.x
            self.root.y = event.y
            
        def stop_move(event):
            # 如果点击的是按钮，不处理窗口移动
            if isinstance(event.widget, tk.Button):
                return
            self.root.x = None
            self.root.y = None
            
        def do_move(event):
            # 如果正在拖动按钮，不移动窗口
            if isinstance(event.widget, tk.Button):
                return
            if hasattr(self.root, 'x') and self.root.x is not None:
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
        toolbar = tk.Frame(self.main_frame, bg="#2b2b2b", height=40)
        toolbar.pack(side="bottom", fill="x", pady=10)
        toolbar.pack_propagate(False)
        
        button_container = tk.Frame(toolbar, bg="#2b2b2b")
        button_container.pack(expand=True, pady=5)
        
        # 提示标签
        hint_label = tk.Label(
            button_container,
            text="拖放文件夹到此处添加",
            bg="#2b2b2b",
            fg="#888888",
            font=self.FONT_NORMAL
        )
        hint_label.pack(side="left", padx=5)
        
        # 添加清空按钮
        clear_btn = tk.Button(
            button_container,
            text="清空",
            command=self._clear_all_shortcuts,
            bg="#E81123",  # 使用红色以示警告
            fg="white",
            activebackground="#FF1A1A",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            font=self.FONT_NORMAL,
            width=4,
            height=1
        )
        clear_btn.pack(side="left", padx=5)
        
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
    def _clear_all_shortcuts(self):
        """清空所有快捷方式"""
        try:
            # 创建确认对话框
            confirm_window = tk.Toplevel(self.root)
            confirm_window.title("确认清空")
            confirm_window.configure(bg="#2b2b2b")
            confirm_window.transient(self.root)
            
            # 设置窗口大小和位置
            window_width = 300
            window_height = 120
            x = self.root.winfo_x() + (self.root.winfo_width() - window_width) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - window_height) // 2
            confirm_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # 添加警告文本
            warning_label = tk.Label(
                confirm_window,
                text="确定要清空所有快捷方式吗？\n此操作不可撤销！",
                bg="#2b2b2b",
                fg="#E81123",
                font=self.FONT_BOLD
            )
            warning_label.pack(pady=10)
            
            # 创建按钮容器
            btn_frame = tk.Frame(confirm_window, bg="#2b2b2b")
            btn_frame.pack(pady=10)
            
            # 确认按钮
            def confirm_clear():
                self.paths_data = {}  # 清空数据
                self._save_paths()    # 保存空数据
                self._create_path_buttons()  # 刷新界面
                confirm_window.destroy()
                self._show_message("已清空所有快捷方式!")
            
            confirm_btn = tk.Button(
                btn_frame,
                text="确认清空",
                command=confirm_clear,
                bg="#E81123",
                fg="white",
                activebackground="#FF1A1A",
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                font=self.FONT_NORMAL
            )
            confirm_btn.pack(side="left", padx=10)
            
            # 取消按钮
            cancel_btn = tk.Button(
                btn_frame,
                text="取消",
                command=confirm_window.destroy,
                bg="#4c5052",
                fg="white",
                activebackground="#5c6062",
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                font=self.FONT_NORMAL
            )
            cancel_btn.pack(side="left", padx=10)
            
            # 设置焦点并使窗口置顶
            confirm_window.focus_set()
            confirm_window.grab_set()
            
        except Exception as e:
            print(f"Error in clear shortcuts: {e}")
            self._show_message("清空失败!")
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
        
        # 创建新按钮
        for index, (name, path) in enumerate(self.paths_data.items()):
            row = index // buttons_per_row
            col = index % buttons_per_row
            
            # 创建按钮框架
            button_frame = tk.Frame(grid_frame, bg="#2b2b2b")
            button_frame.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
            
            # 设置按钮样式
            button_style = {
                "bg": "#4c5052",
                "fg": "white",
                "activebackground": "#5c6062",
                "activeforeground": "white",
                "relief": "flat",
                "cursor": "hand2",
                "width": 20,
                "height": 2,
                "font": self.FONT_BOLD
            }
            
            # 访问按钮
            btn = tk.Button(
                button_frame,
                text=name,
                command=lambda p=path: self._on_button_click(p),
                **button_style
            )
            btn.pack(side="left", padx=5, expand=True)
            
            # 创建右键菜单
            menu = tk.Menu(btn, tearoff=0, bg="#2b2b2b", fg="white", 
                          activebackground="#E81123", activeforeground="white",
                          font=self.FONT_NORMAL)
            menu.add_command(
                label="删除",
                command=lambda n=name: self._delete_path(n),
                font=self.FONT_NORMAL
            )
            
            # 绑定右键事件
            def show_menu(event, m=menu):
                m.post(event.x_root, event.y_root)
            
            btn.bind("<Button-3>", show_menu)
            btn.bind("<Control-Button-1>", show_menu)
        
        # 配置网格列的权重
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
    def _swap_buttons(self, button1, button2):
        """交换两个按钮的位置"""
        idx1 = list(self.paths_data.keys()).index(button1.path_name)
        idx2 = list(self.paths_data.keys()).index(button2.path_name)
        
        if idx1 != idx2:
            keys = list(self.paths_data.keys())
            keys[idx1], keys[idx2] = keys[idx2], keys[idx1]
            
            new_paths_data = {}
            for key in keys:
                new_paths_data[key] = self.paths_data[key]
            
            self.paths_data = new_paths_data
            self._create_path_buttons()
    def _open_path(self, path):
        """打开文件夹"""
        if os.path.exists(path):
            subprocess.run(['explorer', path])
            
    def _delete_path(self, name):
        """删除路径"""
        if name in self.paths_data:
            del self.paths_data[name]
            self._save_paths()
            self._create_path_buttons()
            self._show_message("已删除!")
    def _load_paths(self):
        """加载保存的路径"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    paths = json.load(f)
                    return paths if paths else {}
            return {}
        except Exception as e:
            print(f"Error loading paths: {e}")
            return {}
            
    def _save_paths(self):
        """保存路径"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.paths_data, f, ensure_ascii=False, indent=2)
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
    def _on_drop(self, event):
        """处理文件夹、快捷方式和文件的拖放"""
        try:
            # 处理路径，移除花括号
            path = event.data.strip('{}')
            
            # Windows 系统下的路径处理
            if os.name == 'nt':
                # 统一路径分隔符
                path = path.replace('\\', '/')
            
            print(f"原始路径: {event.data}")
            print(f"处理后路径: {path}")
            
            try:
                # 尝试直接使用路径
                if os.path.exists(path):
                    print(f"路径直接存在")
                else:
                    # 如果路径不存在，尝试不同的编码方式
                    encoded_path = path.encode('utf-8').decode('utf-8')
                    if os.path.exists(encoded_path):
                        path = encoded_path
                        print(f"使用UTF-8编码路径")
                    else:
                        encoded_path = path.encode('gbk').decode('gbk')
                        if os.path.exists(encoded_path):
                            path = encoded_path
                            print(f"使用GBK编码路径")
            except Exception as e:
                print(f"路径编码处理错误: {e}")
            
            print(f"最终路径: {path}")
            print(f"路径是否存在: {os.path.exists(path)}")
            print(f"是否是文件夹: {os.path.isdir(path)}")
            
            # 检查是否是快捷方式
            if path.lower().endswith('.lnk'):
                try:
                    display_name, target_path, arguments, working_dir = self._get_shortcut_info(path)
                    if display_name:
                        print(f"检测到快捷方式: {display_name} -> {target_path}")
                        
                        # 如果名称已存在，添加数字后缀
                        base_name = display_name
                        counter = 1
                        while display_name in self.paths_data:
                            display_name = f"{base_name}_{counter}"
                            counter += 1
                        
                        # 存储程序信息
                        program_info = {
                            'path': target_path,
                            'arguments': arguments,
                            'working_dir': working_dir or os.path.dirname(target_path)
                        }
                        
                        self.paths_data[display_name] = f"program:{json.dumps(program_info, ensure_ascii=False)}"
                        self._save_paths()
                        self._create_path_buttons()
                        self._show_message("快捷方式已添加!")
                        return
                except Exception as e:
                    print(f"处理快捷方式时出错: {e}")
                    self._show_message("添加快捷方式失败!")
                    return
            
            # 检查是否是文件夹
            if os.path.isdir(path):
                print(f"检测到文件夹: {path}")
                try:
                    name = os.path.basename(path)
                    base_name = name
                    counter = 1
                    while name in self.paths_data:
                        name = f"{base_name}_{counter}"
                        counter += 1
                    
                    # 存储规范化的路径
                    self.paths_data[name] = path.replace('\\', '/')
                    self._save_paths()
                    self._create_path_buttons()
                    self._show_message("文件夹已添加!")
                    return
                except Exception as e:
                    print(f"处理文件夹时出错: {e}")
                    self._show_message("添加文件夹失败!")
                    return

            # 检查是否是文件
            if os.path.isfile(path):
                file_ext = os.path.splitext(path)[1].lower()
                print(f"检测到文件，扩展名: {file_ext}")
                
                # 检查是否是视频文件
                if file_ext in self.SUPPORTED_FORMATS["视频"]:
                    try:
                        name = os.path.basename(path)
                        base_name = name
                        counter = 1
                        while name in self.paths_data:
                            name = f"{base_name}_{counter}"
                            counter += 1
                        
                        display_name = f"🎬 {name}"
                        print(f"创建视频快捷方式: {display_name}")
                        
                        # 存储文件信息
                        file_info = {
                            'path': path,
                            'type': "视频"
                        }
                        
                        self.paths_data[display_name] = f"file:{json.dumps(file_info, ensure_ascii=False)}"
                        self._save_paths()
                        self._create_path_buttons()
                        self._show_message("视频已添加!")
                        return
                    except Exception as e:
                        print(f"处理视频文件时出错: {e}")
                        self._show_message("添加视频失败!")
                        return
                
                # 检查其他文件类型
                for file_type, extensions in self.SUPPORTED_FORMATS.items():
                    if file_ext in extensions:
                        try:
                            name = os.path.basename(path)
                            base_name = name
                            counter = 1
                            while name in self.paths_data:
                                name = f"{base_name}_{counter}"
                                counter += 1
                            
                            icon = "📄"  # 默认文档图标
                            if file_type == "图片":
                                icon = "🖼️"
                            elif file_type == "视频":
                                icon = "🎬"
                            
                            display_name = f"{icon} {name}"
                            print(f"创建{file_type}快捷方式: {display_name}")
                            
                            file_info = {
                                'path': path,
                                'type': file_type
                            }
                            
                            self.paths_data[display_name] = f"file:{json.dumps(file_info, ensure_ascii=False)}"
                            self._save_paths()
                            self._create_path_buttons()
                            self._show_message(f"{file_type}已添加!")
                            return
                        except Exception as e:
                            print(f"处理{file_type}文件时出错: {e}")
                            continue
            
            # 如果都不匹配，显示错误信息
            print(f"不支持的文件类型: {path}")
            self._show_message("不支持的文件类型!")
            
        except Exception as e:
            print(f"拖放处理时出错: {e}")
            self._show_message(f"添加失败: {str(e)}")
    def _get_shortcut_info(self, shortcut_path):
        """获取快捷方式信息"""
        try:
            print(f"Getting info for: {shortcut_path}")
            
            # 获取不带扩展名的文件名作为显示名称
            name = os.path.splitext(os.path.basename(shortcut_path))[0]
            
            # 软件特征识别配置
            software_patterns = {
                "blender": {
                    "name": "Blender",
                    "patterns": ["blender"],
                    "version_pattern": r"(\d+\.\d+)",
                    "icon": "🎨"
                },
                "unreal": {
                    "name": "虚幻引擎",
                    "patterns": ["unreal", "ue"],
                    "version_pattern": r"(\d+\.?\d*)",
                    "icon": "🎮"
                },
                "adobe": {
                    "name": "Adobe",
                    "patterns": ["photoshop", "illustrator", "premiere", "after effects"],
                    "apps": {
                        "photoshop": "Photoshop",
                        "illustrator": "Illustrator",
                        "premiere": "Premiere Pro",
                        "after effects": "After Effects",
                        "lightroom": "Lightroom",
                        "indesign": "InDesign",
                        "acrobat": "Acrobat"
                    },
                    "icon": "🎨"
                },
                "unity": {
                    "name": "Unity",
                    "patterns": ["unity"],
                    "version_pattern": r"(\d+\.\d+)",
                    "icon": "🎮"
                },
                "visual_studio": {
                    "name": "Visual Studio",
                    "patterns": ["visual studio", "vs"],
                    "version_pattern": r"(\d+)",
                    "icon": "💻"
                },
                "office": {
                    "name": "Office",
                    "patterns": ["word", "excel", "powerpoint", "outlook"],
                    "apps": {
                        "word": "Word",
                        "excel": "Excel",
                        "powerpoint": "PowerPoint",
                        "outlook": "Outlook"
                    },
                    "icon": "📊"
                },
                "browser": {
                    "name": "浏览器",
                    "patterns": ["chrome", "firefox", "edge", "opera"],
                    "apps": {
                        "chrome": "Chrome",
                        "firefox": "Firefox",
                        "edge": "Edge",
                        "opera": "Opera"
                    },
                    "icon": "🌐"
                },
                "game": {
                    "name": "游戏",
                    "patterns": ["steam", "epic", "game", "ubisoft", "origin"],
                    "icon": "🎮"
                }
            }

            # 检测软件类型并获取显示名称
            display_name = name
            icon = ""
            name_lower = name.lower()
            path_lower = shortcut_path.lower()

            for software, info in software_patterns.items():
                if any(pattern in name_lower or pattern in path_lower for pattern in info["patterns"]):
                    # 基础名称
                    display_name = info["name"]
                    icon = info.get("icon", "")

                    # 版本号检测
                    if "version_pattern" in info:
                        version_match = re.search(info["version_pattern"], name)
                        if version_match:
                            display_name = f"{display_name} {version_match.group(1)}"

                    # 具体应用检测
                    if "apps" in info:
                        for app_pattern, app_name in info["apps"].items():
                            if app_pattern in name_lower or app_pattern in path_lower:
                                display_name = f"{info['name']} {app_name}"
                                break

                    display_name = f"{icon} {display_name}".strip()
                    break

            # 处理快捷方式信息
            if shortcut_path.lower().endswith('.exe'):
                return display_name, shortcut_path, "", os.path.dirname(shortcut_path)

            try:
                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(shortcut_path)
                target_path = shortcut.Targetpath
                arguments = shortcut.Arguments
                working_dir = shortcut.WorkingDirectory or os.path.dirname(shortcut_path)
                
                if not target_path or not os.path.exists(target_path):
                    return display_name, shortcut_path, "", os.path.dirname(shortcut_path)
                
                return display_name, target_path, arguments, working_dir
                
            except Exception as e:
                print(f"Failed to read shortcut info: {e}")
                return display_name, shortcut_path, "", os.path.dirname(shortcut_path)
            
        except Exception as e:
            print(f"Error in _get_shortcut_info: {e}")
            return name, shortcut_path, "", os.path.dirname(shortcut_path)
    def _clean_name(self, original_name):
        """清理名称"""
        try:
            # 常见的需要清理的后缀和前缀
            clean_terms = [
                "- shortcut", "shortcut", ".exe", ".lnk",
                "launcher", "start", "run",
                # 游戏平台
                "steam", "epic", "ubisoft", "ea", "origin", 
                "battle.net", "battlenet", "riot", "rockstar",
                # 版本标识
                "x64", "x86", "(x64)", "(x86)", "64-bit", "32-bit",
                # 其他常见后缀
                "setup", "install", "uninstall",
                # 特殊字符
                "™", "®", "©"
            ]
            
            display_name = original_name
            
            # 移除括号及其内容
            display_name = re.sub(r'\([^)]*\)', '', display_name)
            display_name = re.sub(r'\[[^\]]*\]', '', display_name)
            
            # 清理指定的术语
            for term in clean_terms:
                if display_name.lower().endswith(term.lower()):
                    display_name = display_name[:-len(term)].strip()
                if display_name.lower().startswith(term.lower()):
                    display_name = display_name[len(term):].strip()
            
            # 清理多余的空格、破折号和下划线
            display_name = display_name.strip(" -_")
            # 将多个空格替换为单个空格
            display_name = ' '.join(display_name.split())
            
            # 特殊处理 UE/虚幻引擎
            if "unreal" in display_name.lower() or "ue" in display_name.lower():
                version_match = re.search(r'(\d+\.?\d*)', display_name)
                if version_match:
                    display_name = f"虚幻引擎 {version_match.group(1)}"
                else:
                    display_name = "虚幻引擎"
            
            # 如果清理后为空，返回原始名称
            return display_name if display_name else original_name
            
        except Exception as e:
            print(f"Error in _clean_name: {e}")  # 调试信息
            return original_name
    def _open_program(self, program_path, arguments=None, working_dir=None):
        """打开程序"""
        try:
            print(f"Attempting to open: {program_path}")
            
            # Blender 特殊处理
            if "blender" in program_path.lower():
                print("Using Blender specific launch method...")
                try:
                    # 直接使用 startfile
                    os.startfile(program_path)
                    return
                except Exception as e:
                    print(f"Blender startfile failed: {e}")
                    # 如果失败，尝试其他方法
                    pass
            
            # 其他特殊软件关键词
            special_keywords = [
                "Adobe", "Photoshop", "Illustrator", "Premiere", "After Effects",
                "Unreal", "Epic Games", "UE4", "UE5",
                "Unity", "Unity Hub"
            ]
            
            is_special = any(keyword.lower() in program_path.lower() for keyword in special_keywords)
            
            if is_special or program_path.lower().endswith('.lnk'):
                print("Using special software handling...")
                
                methods = [
                    # 方法1: 直接使用 startfile
                    lambda: os.startfile(program_path),
                    
                    # 方法2: 使用 shell execute 和工作目录
                    lambda: subprocess.Popen(f'start "" "{program_path}"', 
                                          shell=True,
                                          cwd=working_dir if working_dir else os.path.dirname(program_path)),
                    
                    # 方法3: 使用完整路径的 shell execute
                    lambda: subprocess.Popen([program_path], 
                                          shell=True,
                                          cwd=working_dir if working_dir else os.path.dirname(program_path)),
                    
                    # 方法4: 使用 cmd start 命令
                    lambda: subprocess.run(['cmd', '/c', 'start', '', program_path], 
                                        shell=True,
                                        cwd=working_dir if working_dir else os.path.dirname(program_path))
                ]
                
                last_error = None
                for i, method in enumerate(methods, 1):
                    try:
                        print(f"Trying launch method {i}...")
                        method()
                        print(f"Method {i} succeeded!")
                        return
                    except Exception as e:
                        last_error = e
                        print(f"Method {i} failed: {e}")
                        continue
                
                if last_error:
                    raise last_error
                
            else:
                # 常规软件处理保持不变...
                if working_dir:
                    if arguments:
                        subprocess.Popen(f'"{program_path}" {arguments}', 
                                       cwd=working_dir, shell=True)
                    else:
                        subprocess.Popen(f'"{program_path}"', 
                                       cwd=working_dir, shell=True)
                else:
                    if arguments:
                        subprocess.Popen(f'"{program_path}" {arguments}', shell=True)
                    else:
                        subprocess.Popen(f'"{program_path}"', shell=True)
                    
        except Exception as e:
            error_msg = f"无法打开程序: {e}"
            print(error_msg)
            self._show_message(error_msg)
    def _on_button_click(self, path):
        """处理按钮点击事件"""
        try:
            if path.startswith("file:"):
                try:
                    file_info = json.loads(path[5:])
                    if self.copy_path_enabled.get():
                        self.root.clipboard_clear()
                        self.root.clipboard_append(file_info['path'])
                        self._show_message("路径已复制!")
                    else:
                        # 对于图片文件，先显示预览
                        if file_info['type'] == "图片":
                            self._show_image_preview(file_info['path'])
                        else:
                            # 其他文件使用默认程序打开
                            os.startfile(file_info['path'])
                except json.JSONDecodeError as e:
                    print(f"Error decoding file info: {e}")
                    self._show_message("文件格式错误!")
            elif path.startswith("program:"):
                # 如果是程序路径，解析完整信息
                try:
                    program_info = json.loads(path[8:])  # 移除 "program:" 前缀
                    if self.copy_path_enabled.get():
                        # 复制程序路径
                        self.root.clipboard_clear()
                        self.root.clipboard_append(program_info['path'])
                        self._show_message("路径已复制!")
                    else:
                        # 运行程序
                        self._open_program(
                            program_info['path'],
                            program_info.get('arguments'),
                            program_info.get('working_dir')
                        )
                except json.JSONDecodeError as e:
                    print(f"Error decoding program info: {e}")
                    self._show_message("路径格式错误!")
            else:
                # 如果是文件夹路径
                if self.copy_path_enabled.get():
                    self.root.clipboard_clear()
                    self.root.clipboard_append(path)
                    self._show_message("路径已复制!")
                else:
                    self._open_path(path)
        except Exception as e:
            print(f"Error in _on_button_click: {e}")
            self._show_message("操作失败!")
    def _is_game_directory(self, path):
        """检查是否是游戏目录"""
        if not os.path.isdir(path):
            return False
            
        # 游戏目录特征
        game_indicators = [
            '.exe',  # 可执行文件
            'steam_api.dll',  # Steam游戏特征
            'UE4Game',  # 虚幻引擎游戏特征
            'UnityPlayer.dll',  # Unity游戏特征
            'GameData',  # 通用游戏数据目录
            'Binaries',  # 游戏二进制文件目录
            'SaveGames'  # 游戏存档目录
        ]
        
        # 检查目录内容
        dir_contents = os.listdir(path)
        exe_files = [f for f in dir_contents if f.lower().endswith('.exe')]
        
        # 检查是否存在游戏特征
        has_indicators = any(indicator.lower() in str(dir_contents).lower() 
                           for indicator in game_indicators)
        
        return bool(exe_files) and has_indicators

    def _check_special_software(self, path):
        """检查是否是特殊软件"""
        path_lower = path.lower()
        
        # 检查是否匹配特殊软件路径
        for software, config in self.SPECIAL_SOFTWARE_PATHS.items():
            for possible_path in config["possible_paths"]:
                if os.path.exists(possible_path) and (
                    path_lower in possible_path.lower() or 
                    possible_path.lower() in path_lower
                ):
                    return {
                        "name": config["name"],
                        "path": possible_path,
                        "icon": config["icon"]
                    }
        return None

    def _add_special_software_shortcut(self, software):
        """添加特殊软件快捷方式"""
        display_name = f"{software['icon']} {software['name']}"
        
        # 如果名称已存在，添加数字后缀
        base_name = display_name
        counter = 1
        while display_name in self.paths_data:
            display_name = f"{base_name}_{counter}"
            counter += 1
        
        # 存储程序信息
        program_info = {
            'path': software['path'],
            'arguments': '',
            'working_dir': os.path.dirname(software['path'])
        }
        
        self.paths_data[display_name] = f"program:{json.dumps(program_info)}"
        self._save_paths()
        self._create_path_buttons()
        self._show_message(f"{software['name']}已添加!")

    def _add_game_shortcut(self, path):
        """添加游戏快捷方式"""
        # 查找主程序
        exe_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.lower().endswith('.exe'):
                    exe_files.append(os.path.join(root, file))
        
        if not exe_files:
            self._show_message("未找到游戏主程序!")
            return
            
        # 尝试找到主程序（通常是较大的exe文件）
        main_exe = max(exe_files, key=lambda f: os.path.getsize(f))
        
        # 获取游戏名称
        game_name = os.path.basename(path)
        display_name = f"🎮 {game_name}"
        
        # 如果名称已存在，添加数字后缀
        base_name = display_name
        counter = 1
        while display_name in self.paths_data:
            display_name = f"{base_name}_{counter}"
            counter += 1
        
        # 存储程序信息
        program_info = {
            'path': main_exe,
            'arguments': '',
            'working_dir': path
        }
        
        self.paths_data[display_name] = f"program:{json.dumps(program_info)}"
        self._save_paths()
        self._create_path_buttons()
        self._show_message("游戏已添加!")
    def _show_image_preview(self, image_path):
        """显示图片预览窗口"""
        try:
            # 如果已经有预览窗口，先关闭它
            if self.preview_window and self.preview_window.winfo_exists():
                self.preview_window.destroy()
            
            # 创建预览窗口
            self.preview_window = tk.Toplevel(self.root)
            self.preview_window.title("图片预览")
            self.preview_window.configure(bg="#2b2b2b")
            
            # 设置窗口大小和位置
            preview_width = self.IMAGE_PREVIEW_SIZE[0] + 40
            preview_height = self.IMAGE_PREVIEW_SIZE[1] + 60
            x = self.root.winfo_x() + (self.root.winfo_width() - preview_width) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - preview_height) // 2
            self.preview_window.geometry(f"{preview_width}x{preview_height}+{x}+{y}")
            
            # 加载并调整图片大小
            image = Image.open(image_path)
            image.thumbnail(self.IMAGE_PREVIEW_SIZE)
            photo = ImageTk.PhotoImage(image)
            
            # 创建图片标签
            image_label = tk.Label(
                self.preview_window,
                image=photo,
                bg="#2b2b2b",
                bd=2,
                relief="solid"
            )
            image_label.image = photo  # 保持引用
            image_label.pack(pady=10)
            
            # 添加文件名标签
            name_label = tk.Label(
                self.preview_window,
                text=os.path.basename(image_path),
                bg="#2b2b2b",
                fg="white",
                font=self.FONT_NORMAL
            )
            name_label.pack(pady=5)
            
            # 添加关闭按钮
            close_btn = tk.Button(
                self.preview_window,
                text="关闭",
                command=self.preview_window.destroy,
                bg="#4c5052",
                fg="white",
                activebackground="#5c6062",
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                font=self.FONT_NORMAL
            )
            close_btn.pack(pady=5)
            
        except Exception as e:
            print(f"Error showing image preview: {e}")
            self._show_message("无法预览图片!")
    def _create_hot_corner_detector(self):
        """创建热区检测器窗口"""
        self.detector = tk.Toplevel(self.root)
        self.detector.withdraw()  # 初始时隐藏
        self.detector.overrideredirect(True)
        self.detector.attributes('-alpha', 0.01)  # 几乎完全透明
        self.detector.attributes('-topmost', True)
        
        # 设置热区位置和大小
        self.detector.geometry(f"{self.hot_corner_size}x{self.hot_corner_size}+0+0")
        
        # 改为绑定鼠标点击事件，而不是进入事件
        self.detector.bind("<Button-1>", self._on_hot_corner_activated)
        
    def _on_minimize(self, event):
        """窗口最小化时激活热区"""
        self.hot_corner_active = True
        self.detector.deiconify()  # 显示热区检测器
        
    def _on_restore(self, event):
        """窗口恢复时禁用热区"""
        self.hot_corner_active = False
        self.detector.withdraw()  # 隐藏热区检测器
        
    def _on_hot_corner_activated(self, event):
        """当点击热区时"""
        if self.hot_corner_active:
            # 恢复窗口
            self.root.deiconify()
            self.root.lift()  # 将窗口置于顶层
            self.root.focus_force()  # 强制获取焦点
            
            # 移动到原来的位置
            x = 20  # 距离左边缘20像素
            y = 20  # 距离上边缘20像素
            self.root.geometry(f"+{x}+{y}")
            
            # 禁用热区
            self.hot_corner_active = False
            self.detector.withdraw()
    def run(self):
        """运行程序"""
        self.root.mainloop()
if __name__ == "__main__":
    app = FolderAccessTool()
    app.run()
