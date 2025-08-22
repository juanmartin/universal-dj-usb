# -*- mode: python ; coding: utf-8 -*-
"""
Optimized PyInstaller spec file for Universal DJ USB GUI.
This file contains all build customizations for size optimization.
"""

# Qt modules to exclude - these are not used by our GUI
qt_excludes = [
    'PySide6.QtNetwork',
    'PySide6.QtOpenGL', 
    'PySide6.QtQuick',
    'PySide6.QtQml',
    'PySide6.QtQmlModels',
    'PySide6.QtQmlWorkerScript',
    'PySide6.QtQmlMeta',
    'PySide6.QtSvg',
    'PySide6.QtDBus',
    'PySide6.QtPdf',
    'PySide6.QtVirtualKeyboard',
    'PySide6.QtVirtualKeyboardQml',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'PySide6.Qt3DCore',
    'PySide6.Qt3DRender',
    'PySide6.QtCharts',
    'PySide6.QtDataVisualization',
    'PySide6.QtMultimedia',
    'PySide6.QtBluetooth',
    'PySide6.QtPositioning',
    'PySide6.QtSensors',
]

# Other frameworks and libraries to exclude
other_excludes = [
    # GUI frameworks we don't use
    'tkinter',
    'PyQt4',
    'PyQt5', 
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
    'pytest-cov',
    'coverage', 
    'mypy',
    'mypy-extensions',
    'black',
    'isort',
    'flake8',
    'pycodestyle',
    'pyflakes', 
    'mccabe',
    'sphinx',
    'docutils',
    'setuptools',
    'pkg_resources',
    'distutils',
    'pip',
    'wheel',
    'tox',
    'virtualenv',
    'pyinstaller-hooks-contrib',  # PyInstaller dev tools
    'importlib-metadata',         # Dependency scanning
    'zipp',                       # Archive handling
    'packaging',                  # Python packaging tools
    'pathspec',                   # File path matching (used by black/mypy)
    'platformdirs',               # Platform directories (used by black)
    'tomli',                      # TOML parsing (used by black/mypy)
    'typing-extensions',          # Type hints (might be needed - test carefully)
    'colorama',                   # Terminal colors (used by dev tools)
    'exceptiongroup',             # Exception handling (pytest)
    'iniconfig',                  # INI config parsing (pytest)
    'pluggy',                     # Plugin system (pytest)
    'markdown-it-py',             # Markdown parsing (rich dependency)
    'mdurl',                      # Markdown URL handling
    'pygments',                   # Syntax highlighting (rich dependency)
    
    # System modules we don't need
    '_bootlocale',
    'doctest',
    'unittest',
    'test',
]

# Combine all exclusions
all_excludes = qt_excludes + other_excludes

a = Analysis(
    ['udj_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],  # No extra data files needed - everything is compiled into the executable
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=all_excludes,
    noarchive=False,
    optimize=2,  # Maximum bytecode optimization
)

print(f"Total binaries: {len(a.binaries)}")

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Universal DJ USB',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip debug symbols
    upx=False,   # Disable UPX (causes issues on macOS)
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
    strip=True,  # Strip debug symbols from libraries
    upx=False,   # Disable UPX
    upx_exclude=[],
    name='Universal DJ USB',
)

app = BUNDLE(
    coll,
    name='Universal DJ USB.app',
    icon='src/universal_dj_usb/assets/icons/icono_1024x1024_1024x1024.icns',
    bundle_identifier='art.juanm.udj',
)
