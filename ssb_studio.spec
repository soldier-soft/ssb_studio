# -*- mode: python ; coding: utf-8 -*-
# PyInstaller Spec for SSB Practice Studio Windows Executable

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

root_dir = Path.cwd()

# Data files to bundle: UI stylesheets, sample content, assets
# Also include PyMuPDF layout resources (required for PyMuPDF 1.23+)
datas = [
    (str(root_dir / 'ui' / 'styles' / '*.qss'), 'ui/styles'),
    (str(root_dir / 'sample_content'), 'sample_content'),
    (str(root_dir / 'assets'), 'assets'),
]
datas += collect_data_files('pymupdf')

hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'sqlite3',
    'reportlab',
    'reportlab.platypus',
    'reportlab.lib',
    'reportlab.lib.colors',
    'reportlab.lib.pagesizes',
    'reportlab.lib.styles',
    'reportlab.lib.units',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'fitz',
    'pymupdf',
    'pytesseract',
]

a = Analysis(
    ['app/main.py'],
    pathex=[str(root_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(root_dir / 'scripts' / 'rthooks' / 'pyi_rth_mupdf.py')],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pymupdf.layout', 'pymupdf_layout', 'onnxruntime', 'onnx'],
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
    name='SSBPracticeStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed desktop application (no terminal popup)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root_dir / 'assets' / 'app_icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SSBPracticeStudio',
)
