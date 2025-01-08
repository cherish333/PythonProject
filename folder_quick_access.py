def _on_drop(self, event):
    """处理文件夹和快捷方式的拖放"""
    try:
        # 获取拖放的路径
        path = event.data
        
        # 如果是 Windows 系统，需要处理路径格式
        if os.name == 'nt':
            path = path.strip('{}"\' ')
            if ' ' in path:
                path = path.split(' ')[0]
        
        print(f"Dropped path: {path}")
        
        # 支持的文件类型
        supported_extensions = {
            # 快捷方式和可执行文件
            'shortcuts': ['.lnk', '.exe'],
            # 视频文件
            'video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
            # 文档文件
            'document': [
                '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', 
                '.txt', '.rtf', '.csv'
            ],
            # 图片文件
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            # 音频文件
            'audio': ['.mp3', '.wav', '.flac', '.m4a', '.ogg'],
            # 压缩文件
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz']
        }
        
        # 获取文件扩展名
        file_ext = os.path.splitext(path)[1].lower()
        
        # 检查是否是支持的文件类型
        is_supported = False
        file_type = None
        for type_name, extensions in supported_extensions.items():
            if file_ext in extensions:
                is_supported = True
                file_type = type_name
                break
        
        # 特殊软件关键词检测
        special_software_keywords = [
            "blender", "unreal", "ue", "unity", "adobe", 
            "visual studio", "vs", "photoshop", "illustrator",
            "premiere", "after effects", "lightroom", "steam",
            "epic games", "office", "chrome", "firefox", "edge"
        ]
        
        is_special_software = any(keyword.lower() in path.lower() 
                                for keyword in special_software_keywords)
        
        # 处理文件
        if os.path.isfile(path) and (is_supported or is_special_software):
            # 获取文件信息
            file_name = os.path.basename(path)
            display_name = os.path.splitext(file_name)[0]
            
            # 如果是特殊软件，使用更友好的显示名称
            if is_special_software:
                display_name = self._get_friendly_software_name(path)
            
            # 添加文件类型标识
            if file_type:
                display_name = f"{display_name} [{file_type}]"
            
            # 如果名称已存在，添加数字后缀
            base_name = display_name
            counter = 1
            while display_name in self.paths_data:
                display_name = f"{base_name}_{counter}"
                counter += 1
            
            # 存储文件信息
            file_info = {
                'path': path,
                'type': file_type or 'program',
                'arguments': '',
                'working_dir': os.path.dirname(path)
            }
            
            # 添加到路径数据
            self.paths_data[display_name] = f"program:{json.dumps(file_info)}"
            self._save_paths()
            self._create_path_buttons()
            self._show_message(f"{file_type or '程序'}已添加!")
            return
            
        # 处理文件夹
        if os.path.exists(path) and os.path.isdir(path):
            name = os.path.basename(path)
            base_name = name
            counter = 1
            while name in self.paths_data:
                name = f"{base_name}_{counter}"
                counter += 1
            
            self.paths_data[name] = path
            self._save_paths()
            self._create_path_buttons()
            self._show_message("文件夹已添加!")
            
    except Exception as e:
        print(f"Error in _on_drop: {e}")
        self._show_message(f"添加失败: {str(e)}")

def _get_friendly_software_name(self, path):
    """获取友好的软件名称"""
    name = os.path.splitext(os.path.basename(path))[0].lower()
    
    # 软件名称映射
    software_names = {
        "blender": "Blender",
        "unreal": "虚幻引擎",
        "ue": "虚幻引擎",
        "unity": "Unity",
        "visual studio": "Visual Studio",
        "vs": "Visual Studio",
        "photoshop": "Photoshop",
        "illustrator": "Illustrator",
        "premiere": "Premiere Pro",
        "after effects": "After Effects",
        "lightroom": "Lightroom",
        "chrome": "Chrome",
        "firefox": "Firefox",
        "edge": "Edge",
        "word": "Word",
        "excel": "Excel",
        "powerpoint": "PowerPoint",
        "steam": "Steam",
        "epic": "Epic Games"
    }
    
    # 尝试匹配软件名称
    for keyword, friendly_name in software_names.items():
        if keyword in name:
            # 尝试提取版本号
            version_match = re.search(r'(\d+\.?\d*)', name)
            if version_match:
                return f"{friendly_name} {version_match.group(1)}"
            return friendly_name
    
    return name 