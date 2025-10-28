# -*- mode: python -*-
# PyInstaller onedir 打包配置
import sys
from pathlib import Path

block_cipher = None

project_dir = Path(__file__).resolve().parent.parent

a = Analysis([
    str(project_dir / "main.py"),
],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        (str(project_dir / "qml"), "qml"),
        (str(project_dir / "assets"), "assets"),
        (str(project_dir / "i18n"), "i18n"),
        (str(project_dir / "sample_data"), "sample_data"),
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='EdgeJSONStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EdgeJSONStudio'
)
