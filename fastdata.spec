# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller onedir spec for FastData (NodeGraphQt + PySide6 desktop app)."""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# NodeGraphQt ships runtime data (icons) under its package; collect it all.
nodegraphqt_datas = collect_data_files("NodeGraphQt")
nodegraphqt_hidden = collect_submodules("NodeGraphQt")

# QtPy is distributed as a single `Qt.py` module; ensure it is pulled in.
qtpy_hidden = collect_submodules("Qt")

# NodeGraphQt does `from Qt import QtSvg`; QtPy maps that to PySide6.QtSvg, which
# PyInstaller's PySide6 hook does not bundle by default.
pyside6_hidden = ["PySide6.QtSvg"]

# App icon asset: main_window.py resolves it via Path(__file__).parent.parent / "assets".
# In a frozen bundle __file__ lives under _MEIPASS/fastdata/ui, so place the asset at
# _MEIPASS/fastdata/assets/app_icon.svg.
asset_datas = [("fastdata/assets/app_icon.svg", "fastdata/assets")]

datas = nodegraphqt_datas + asset_datas
hiddenimports = nodegraphqt_hidden + qtpy_hidden + pyside6_hidden

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FastData",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="FastData",
)
