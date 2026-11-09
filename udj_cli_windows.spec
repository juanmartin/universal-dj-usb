# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Universal DJ USB CLI - Windows
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
ORIGINAL_FILENAME = f"udj-{APP_VERSION}-windows-{ARCH}.exe"
VERSION_FILE = Path("build") / "windows_version_info_cli.txt"
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
         StringStruct('FileDescription', 'Universal DJ USB CLI'),
         StringStruct('FileVersion', '{APP_VERSION}'),
         StringStruct('InternalName', 'udj'),
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

# Windows onefile executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='udj',
    version=str(VERSION_FILE),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Strip not available on Windows
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/universal_dj_usb/assets/icons/icono.ico',
)
