# -*- mode: python ; coding: utf-8 -*-
"""
Optimized PyInstaller spec file for Universal DJ USB CLI.
This file contains all build customizations for size optimization.
"""

import sys

# Libraries to exclude - CLI doesn't need GUI frameworks
cli_excludes = [
    # GUI frameworks
    'tkinter',
    'PyQt4',
    'PyQt5',
    'PySide6',
    'wx',
    'kivy',
    
    # Scientific/ML libraries  
    'numpy',
    'scipy',
    'pandas',
    'matplotlib',
    'seaborn',
    'sklearn',
    'torch',
    'tensorflow',
    'cv2',
    'PIL',
    'Pillow',
    
    # Development tools
    'pytest',
    'coverage',
    'mypy',
    'black',
    'isort',
    'flake8',
    'sphinx',
    'docutils',
    'setuptools',
    'pkg_resources',
    'distutils',
    'pip',
    'wheel',
    'tox',
    'virtualenv',
    
    # System modules we don't need
    '_bootlocale',
]

a = Analysis(
    ['udj_cli.py'],
    pathex=[],
    binaries=[],
    datas=[],  # No extra data files needed - everything is compiled into the executable
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=cli_excludes,
    noarchive=False,
    optimize=2,  # Maximum bytecode optimization
)

pyz = PYZ(a.pure)

# Determine icon based on platform
icon_path = None
if sys.platform == 'darwin':
    icon_path = 'src/universal_dj_usb/assets/icons/icono_1024x1024_1024x1024.icns'
elif sys.platform in ['win32', 'cygwin']:
    icon_path = 'src/universal_dj_usb/assets/icons/icono.ico'
# Linux doesn't typically use icons in CLI executables

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='udj',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,   # Strip debug symbols
    upx=False,    # Disable UPX (can cause issues)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
