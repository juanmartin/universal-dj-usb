# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Universal DJ USB GUI - Windows
Optimized for Windows portable executable (onefile)
"""

import platform
import re
from pathlib import Path

import tomllib


def _version_tuple(version: str) -> tuple[int, int, int, int]:
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        return (0, 0, 0, 0)
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)), 0)


APP_VERSION = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))[
    "project"
]["version"]
_MACHINE = platform.machine().lower()
if _MACHINE in {"amd64", "x86_64"}:
    ARCH = "x64"
elif _MACHINE in {"arm64", "aarch64"}:
    ARCH = "arm64"
else:
    ARCH = "x86"
ORIGINAL_FILENAME = f"Universal-DJ-USB-{APP_VERSION}-windows-{ARCH}.exe"
VERSION_FILE = Path("build") / "windows_version_info_gui.txt"
VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
VERSION_FILE.write_text(
    f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={_version_tuple(APP_VERSION)},
    prodvers={_version_tuple(APP_VERSION)},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'jaunmatrin'),
         StringStruct('FileDescription', 'Universal DJ USB'),
         StringStruct('FileVersion', '{APP_VERSION}'),
         StringStruct('InternalName', 'Universal DJ USB'),
         StringStruct('LegalCopyright', 'Copyright (c) 2026 jaunmatrin'),
         StringStruct('OriginalFilename', '{ORIGINAL_FILENAME}'),
         StringStruct('ProductName', 'Universal DJ USB'),
         StringStruct('ProductVersion', '{APP_VERSION}')])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""",
    encoding="utf-8",
)

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

# Combine all exclusions
all_excludes = qt_excludes + other_excludes

a = Analysis(
    ['udj_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=all_excludes,
    noarchive=False,
    optimize=2,
)

print(f"Total binaries: {len(a.binaries)}")

pyz = PYZ(a.pure)

# Windows onefile executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Universal DJ USB',
    version=str(VERSION_FILE),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Strip not available on Windows
    upx=False,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/universal_dj_usb/assets/icons/icono.ico',
)
