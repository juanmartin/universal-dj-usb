# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Universal DJ USB CLI - macOS
Optimized for macOS binary (onedir)
"""

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
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=cli_excludes,
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

# macOS onefile executable (includes all binaries like main branch)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='udj',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/universal_dj_usb/assets/icons/icono_1024x1024_1024x1024.icns',
)
