# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

ttk_datas, ttk_binaries, ttk_hidden = collect_all("ttkthemes")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=ttk_binaries,
    datas=ttk_datas,
    hiddenimports=[
        *ttk_hidden,
        *collect_submodules("ttkthemes"),
        "PIL.ImageTk",
        "PIL._tkinter_finder",
        "qrcode",
        "qrcode.image.pil",
        "winotify",
        "openpyxl",
        "pandas",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CalculadoraCostos-PUBLISTIK",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
