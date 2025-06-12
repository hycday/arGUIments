# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Location of your custom Python installation
tcl_lib = r'C:\Users\d\.pyenv\pyenv-win\versions\3.10.11\tcl\tcl8.6'
tk_lib  = r'C:\Users\d\.pyenv\pyenv-win\versions\3.10.11\tcl\tk8.6'
dll_dir = r'C:\Users\d\.pyenv\pyenv-win\versions\3.10.11\DLLs'

# Collect pycaw and comtypes data
pycaw_datas = collect_data_files('pycaw')
comtypes_binaries = collect_dynamic_libs('comtypes')

# Add tkinter DLLs manually
tkinter_binaries = [
    (os.path.join(dll_dir, 'tcl86t.dll'), '.'),
    (os.path.join(dll_dir, 'tk86t.dll'), '.'),
]

# Include icons
extra_datas = [
    ('icon.ico', '.'),
    (tcl_lib, 'lib/tcl8.6'),
    (tk_lib, 'lib/tk8.6'),
]

image_assets = [
    ('show.png', '.'),
    ('hide.png', '.'),     
    ('settings.png', '.'),     
    ('about.png', '.'),     
    ('add.png', '.'),     
    ('delete.png', '.'),     
    ('stop.png', '.'),     
    ('run.png', '.'),     
    ('edit.png', '.'),     
]


# Combine all data and binaries
datas = pycaw_datas + extra_datas + image_assets
binaries = comtypes_binaries + tkinter_binaries

hiddenimports = [
    'tkinter',
    'pystray',
    'pystray._win32',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'pycaw',
    'pycaw.pycaw',
    'comtypes',
    'comtypes.client'
]

block_cipher = None

a = Analysis(
    ['arGUIments.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
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
    name='arGUIments',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # This is equivalent to --windowed
    icon='icon.ico'
)