import tkinter as tk
from tkinter import filedialog
import json
import os
import subprocess
from tkinterdnd2 import *
import winshell
from win32com.client import Dispatch
import re
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
    # 恢复原来的字体设置
    FONT_FAMILY = "Microsoft YaHei"
    FONT_NORMAL = ("Microsoft YaHei", 9)
    FONT_BOLD = ("Microsoft YaHei", 11, "bold")
    FONT_TITLE = ("Microsoft YaHei", 10)
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
        
        # 定义不同类型按钮的颜色
        button_colors = {
            "folder": {
                "bg": "#4c5052",
                "active_bg": "#5c6062"
            },
            "shortcut": {
                "bg": "#3c4042",
                "active_bg": "#4c5052"
            },
            "special": {  # 特殊软件（如Blender、UE等）
                "bg": "#2d4052",
                "active_bg": "#3d5062"
            }
        }
        
        # 创建新按钮
        for index, (name, path) in enumerate(self.paths_data.items()):
            row = index // buttons_per_row
            col = index % buttons_per_row
            
            # 创建按钮框架
            button_frame = tk.Frame(grid_frame, bg="#2b2b2b")
            button_frame.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
            
            # 确定按钮类型和颜色
            if path.startswith("program:"):
                # 检查是否是特殊软件
                is_special = any(keyword.lower() in path.lower() for keyword in [
                    "blender", "unreal", "ue", "unity", "adobe", "visual studio",
                    "photoshop", "illustrator", "premiere"
                ])
                colors = button_colors["special"] if is_special else button_colors["shortcut"]
            else:
                colors = button_colors["folder"]
            
            # 设置按钮样式
            button_style = {
                "bg": colors["bg"],
                "fg": "white",
                "activebackground": colors["active_bg"],
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
    def _on_drop(self, event):
        """处理文件夹和快捷方式的拖放"""
        try:
            # 获取拖放的路径
            path = event.data
            
            # 如果是 Windows 系统，需要处理路径格式
            if os.name == 'nt':
                # 移除可能的花括号和引号
                path = path.strip('{}"\' ')
                # 处理多个文件的情况，我们只取第一个
                if ' ' in path:
                    path = path.split(' ')[0]
            
            print(f"Dropped path: {path}")  # 调试信息
            
            # 检查是否是快捷方式、可执行文件或特殊软件
            is_special_software = any(keyword.lower() in path.lower() for keyword in [
                "blender", "unreal", "ue", "unity", "adobe"
            ])
            
            if path.lower().endswith(('.lnk', '.exe')) or is_special_software:
                print(f"Processing special software/shortcut: {path}")  # 调试信息
                
                # 对于特殊软件，创建一个虚拟的快捷方式信息
                if is_special_software and not path.lower().endswith(('.lnk', '.exe')):
                    # 尝试在路径中查找可执行文件
                    exe_files = []
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if file.lower().endswith('.exe'):
                                exe_files.append(os.path.join(root, file))
                    
                    if exe_files:
                        # 使用找到的第一个可执行文件
                        target_path = exe_files[0]
                        display_name = os.path.basename(path)  # 使用文件夹名称
                    else:
                        # 如果没有找到可执行文件，使用文件夹路径
                        target_path = path
                        display_name = os.path.basename(path)
                    
                    working_dir = path
                    arguments = ""
                else:
                    # 正常处理快捷方式或可执行文件
                    display_name, target_path, arguments, working_dir = self._get_shortcut_info(path)
                
                if display_name:
                    print(f"Got info - Name: {display_name}, Target: {target_path}")  # 调试信息
                    
                    # 如果名称已存在，添加数字后缀
                    base_name = display_name
                    counter = 1
                    while display_name in self.paths_data:
                        display_name = f"{base_name}_{counter}"
                        counter += 1
                    
                    # 存储完整的程序信息
                    program_info = {
                        'path': target_path,
                        'arguments': arguments,
                        'working_dir': working_dir or os.path.dirname(target_path)
                    }
                    
                    # 添加新程序路径
                    self.paths_data[display_name] = f"program:{json.dumps(program_info)}"
                    self._save_paths()
                    self._create_path_buttons()
                    self._show_message("快捷方式已添加!")
                    return
            
            # 处理文件夹
            if os.path.exists(path) and os.path.isdir(path) and not is_special_software:
                name = os.path.basename(path)
                
                # 如果名称已存在，添加数字后缀
                base_name = name
                counter = 1
                while name in self.paths_data:
                    name = f"{base_name}_{counter}"
                    counter += 1
                
                # 添加新路径
                self.paths_data[name] = path
                self._save_paths()
                self._create_path_buttons()
                self._show_message("文件夹已添加!")
                
        except Exception as e:
            print(f"Error in _on_drop: {e}")  # 调试信息
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
            if path.startswith("program:"):
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
    def run(self):
        """运行程序"""
        self.root.mainloop()
if __name__ == "__main__":
    app = FolderAccessTool()
    app.run()
