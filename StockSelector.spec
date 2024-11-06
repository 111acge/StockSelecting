# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import site
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

def find_mini_racer_dll():
    """查找 mini_racer.dll 文件的位置"""
    search_paths = []
    search_paths.extend(site.getsitepackages())
    user_site = site.getusersitepackages()
    if user_site:
        search_paths.append(user_site)
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        search_paths.append(os.path.join(sys.prefix, 'Lib', 'site-packages'))
    for path in search_paths:
        dll_path = os.path.join(path, 'py_mini_racer', 'mini_racer.dll')
        if os.path.exists(dll_path):
            return dll_path
    return None

def find_akshare_data():
    """查找并收集 akshare 数据文件"""
    search_paths = []
    search_paths.extend(site.getsitepackages())
    user_site = site.getusersitepackages()
    if user_site:
        search_paths.append(user_site)
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        search_paths.append(os.path.join(sys.prefix, 'Lib', 'site-packages'))

    akshare_data = []
    for path in search_paths:
        akshare_path = os.path.join(path, 'akshare')
        if os.path.exists(akshare_path):
            # 添加 calendar.json
            calendar_path = os.path.join(akshare_path, 'file_fold', 'calendar.json')
            if os.path.exists(calendar_path):
                akshare_data.append((calendar_path, os.path.join('akshare', 'file_fold')))

            # 添加其他数据文件
            for root, dirs, files in os.walk(akshare_path):
                for file in files:
                    if file.endswith('.json') or file.endswith('.csv'):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(root, akshare_path)
                        akshare_data.append((full_path, os.path.join('akshare', rel_path)))
    return akshare_data

# 基础配置
block_cipher = None

# 收集所有需要的包
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    'qdarkstyle',
    'qdarkstyle.palette',
    'qdarkstyle.style_rc',
    'qtsass',
    'akshare',
    'pandas',
    'numpy',
    'yaml',
    'openpyxl',
    'py_mini_racer',
    'charset_normalizer.md__mypyc',
    'charset_normalizer',
] + collect_submodules('akshare')

# 收集所有的包数据
datas = [
    ('config', 'config'),
    ('gui', 'gui'),
    ('core', 'core'),
    ('utils', 'utils'),
]

# 验证和处理图标文件
icon_file = os.path.abspath('C:/Users/29193/PycharmProjects/StockSelecting/market.ico')
if not os.path.exists(icon_file):
    print(f"Warning: Icon file not found at {icon_file}")
    icon_path = None
else:
    print(f"Found icon file at {icon_file}")

# 检查并添加 .venv/library 目录
venv_library_path = os.path.join('.venv', 'library')
if os.path.exists(venv_library_path):
    datas.append((venv_library_path, 'library'))

# 添加数据文件
datas.extend(find_akshare_data())
datas.extend(collect_data_files('akshare'))
datas.extend(collect_data_files('qdarkstyle'))

# 收集依赖包的数据和二进制文件
binaries = []
for pkg in ['PyQt6', 'qdarkstyle']:
    try:
        pkg_data = collect_all(pkg)
        datas.extend(pkg_data[0])
        binaries.extend(pkg_data[1])
        hiddenimports.extend(pkg_data[2])
    except Exception as e:
        print(f"Warning: Failed to collect {pkg} data: {e}")

# 处理 mini_racer.dll
mini_racer_dll = find_mini_racer_dll()
if mini_racer_dll:
    binaries.append((mini_racer_dll, '.'))
    binaries.append((mini_racer_dll, '_internal'))
else:
    print("WARNING: Could not find mini_racer.dll!")

# 尝试收集 qdarkstyle 的子模块
try:
    hiddenimports.extend(collect_submodules('qdarkstyle', filter=lambda name: 'utils' not in name))
except Exception as e:
    print(f"Warning: Failed to collect some qdarkstyle submodules: {e}")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
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

# 去重数据文件
seen = set()
a.datas = [x for x in a.datas if not (x[0] in seen or seen.add(x[0]))]

# 去重二进制文件
seen = set()
a.binaries = [x for x in a.binaries if not (x[0] in seen or seen.add(x[0]))]

# 创建 PYZ 归档
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 创建单个可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='StockSelector',
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
    icon=icon_file,
)