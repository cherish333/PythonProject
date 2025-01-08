# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 收集所有需要的数据文件
datas = []
datas += collect_data_files('tkinterdnd2')

# 收集所有需要的隐藏导入
hiddenimports = [
    'winshell',
    'win32com',
    'win32com.client',
    'win32com.shell',
    'win32api',
    'win32con',
    'win32gui',
    'pythoncom',
    'pywintypes',
    'tkinterdnd2',
    'PIL',
    'PIL._tkinter_finder',
]

a = Analysis(
    ['QuickLaunch.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QuickLaunch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 如果没有图标文件，请注释掉下面这行
    # icon='IG.ico'
)
