# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for the legacy macOS 10.14 (Mojave) GUI build.

Differences from udj_gui_macos.spec:
- Reads the version without tomllib, because the legacy build uses Python 3.10.
- Keeps QtQml/QtQuick in the bundle; PySide6 6.3.2 needs them on macOS 10.14.
- Adds the PySide6 runtime hook used by the Mojave build.
- Declares macOS 10.14 as the minimum system version.
"""

import re
from pathlib import Path

APP_VERSION = re.search(
    r'^version = "([^"]+)"',
    Path("pyproject.toml").read_text(encoding="utf-8"),
    re.MULTILINE,
).group(1)

# Qt modules to exclude. QtQml/QtQuick are intentionally not excluded:
# libpyside6 6.3.2 loads them on macOS 10.14 even though the app does not
# import them directly.
qt_excludes = [
    'PySide6.QtNetwork',
    'PySide6.QtOpenGL',
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
    'pyinstaller-hooks-contrib',
    'importlib-metadata',
    'zipp',
    'packaging',
    'pathspec',
    'platformdirs',
    'tomli',
    'typing-extensions',
    'colorama',
    'exceptiongroup',
    'iniconfig',
    'pluggy',
    'markdown-it-py',
    'mdurl',
    'pygments',

    # System modules we don't need
    '_bootlocale',
    'doctest',
    'unittest',
    'test',
]

hidden_imports = [
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtQmlModels',
]

a = Analysis(
    ['udj_gui.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_pyside6_macos.py'],
    excludes=qt_excludes + other_excludes,
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

# macOS onedir executable (exclude binaries for proper COLLECT structure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Universal DJ USB',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/universal_dj_usb/assets/icons/icono_1024x1024_1024x1024.icns',
)

# Create COLLECT for onedir build
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=False,
    upx_exclude=[],
    name='Universal DJ USB',
)

# Create macOS app bundle
app = BUNDLE(
    coll,
    name='Universal DJ USB.app',
    icon='src/universal_dj_usb/assets/icons/icono_1024x1024_1024x1024.icns',
    bundle_identifier='art.juanm.udj',
    info_plist={
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleVersion': APP_VERSION,
        'CFBundleDisplayName': 'Universal DJ USB',
        'LSMinimumSystemVersion': '10.14',
        'NSHumanReadableCopyright': 'Copyright (c) 2026 jaunmatrin',
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'NSHighResolutionCapable': True,
    },
)
