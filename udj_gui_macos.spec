# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Universal DJ USB GUI - macOS
Optimized for macOS app bundle (onedir)
"""

import os
from pathlib import Path

# Qt modules to exclude - these are not used by our GUI
# NOTE: QtQml and QtQuick removed from excludes for PySide6 6.2.0 compatibility on macOS 10.14
# The libpyside6 core library requires these internally even if not used directly
qt_excludes = [
    'PySide6.QtNetwork',
    'PySide6.QtOpenGL',
    # 'PySide6.QtQuick',  # Commented out - required by libpyside6 in 6.2.0
    # 'PySide6.QtQml',  # Commented out - required by libpyside6 in 6.2.0
    # 'PySide6.QtQmlModels',  # Commented out - related to QtQml
    # 'PySide6.QtQmlWorkerScript',  # Commented out - related to QtQml
    # 'PySide6.QtQmlMeta',  # Commented out - related to QtQml
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

# Force include QtQml modules that PySide6 6.2.0 needs on macOS 10.14
# These are required by libpyside6 core library even if not explicitly imported
hidden_imports = [
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtQmlModels',
]

# Find and manually add Qt framework libraries that PySide6 needs
# PyInstaller sometimes misses these on older macOS versions
qt_binaries = []

# Try to find PySide6 Qt libraries
try:
    import PySide6
    pyside6_path = Path(PySide6.__file__).parent
    qt_lib_path = pyside6_path / "Qt" / "lib"
    
    print(f"\n=== Looking for Qt libraries in: {qt_lib_path} ===")
    
    if qt_lib_path.exists():
        # Find QtQml framework/library
        qt_frameworks = [
            'QtQml.framework',
            'QtQuick.framework',
        ]
        
        for fw in qt_frameworks:
            fw_path = qt_lib_path / fw
            if fw_path.exists():
                # Add the entire framework
                print(f"Found framework: {fw}")
                # For frameworks, we need to add the actual library inside
                lib_file = fw_path / fw.replace('.framework', '')
                if lib_file.exists():
                    qt_binaries.append((str(lib_file), 'PySide6/Qt/lib'))
                    print(f"  Added: {lib_file}")
        
        # Also look for dylib files directly
        for dylib in qt_lib_path.glob("libQt6Qml*.dylib"):
            qt_binaries.append((str(dylib), 'PySide6/Qt/lib'))
            print(f"Found dylib: {dylib.name}")
            
        for dylib in qt_lib_path.glob("libQt6Quick*.dylib"):
            qt_binaries.append((str(dylib), 'PySide6/Qt/lib'))
            print(f"Found dylib: {dylib.name}")
            
    print(f"Total Qt binaries to add: {len(qt_binaries)}")
    print("=" * 50)
    
except Exception as e:
    print(f"Warning: Could not find Qt libraries: {e}")

a = Analysis(
    ['udj_gui.py'],
    pathex=[],
    binaries=qt_binaries,
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_pyside6_macos.py'],
    excludes=all_excludes,
    noarchive=False,
    optimize=2,
)

print(f"Total binaries: {len(a.binaries)}")

# Debug: Check if QtQml is included
print("\n=== Checking for QtQml in binaries ===")
qtqml_found = False
for binary_name, binary_path, binary_type in a.binaries:
    if 'QtQml' in binary_name or 'QtQml' in binary_path:
        print(f"Found QtQml: {binary_name} -> {binary_path}")
        qtqml_found = True

if not qtqml_found:
    print("WARNING: QtQml not found in binaries! This may cause runtime errors.")
    print("PySide6 6.2.0 on macOS 10.14 requires QtQml framework.")
else:
    print("✓ QtQml found in binaries")
print("=" * 50)

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
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleVersion': '0.1.0',
        'CFBundleDisplayName': 'Universal DJ USB',
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'NSHighResolutionCapable': True,
    },
)

# Fix @rpath issues for PySide6 on macOS 10.14
# The libpyside6 library needs to find QtQml in the app bundle structure
print("\n=== Fixing @rpath for macOS app bundle ===")
try:
    import subprocess
    
    app_path = Path('dist/Universal DJ USB.app')
    frameworks_path = app_path / 'Contents/Frameworks'
    
    # Find libpyside6 and fix its rpath
    libpyside6 = list(frameworks_path.glob('**/libpyside6*.dylib'))
    
    if libpyside6:
        for lib in libpyside6:
            print(f"Fixing rpath for: {lib.name}")
            
            # Add rpath to find Qt libraries in the bundle
            rpaths_to_add = [
                '@loader_path/PySide6/Qt/lib',
                '@loader_path/Qt/lib',
                '@loader_path/../Frameworks/PySide6/Qt/lib',
                '@executable_path/../Frameworks/PySide6/Qt/lib',
            ]
            
            for rpath in rpaths_to_add:
                try:
                    subprocess.run(
                        ['install_name_tool', '-add_rpath', rpath, str(lib)],
                        check=False,  # Don't fail if rpath already exists
                        capture_output=True
                    )
                except Exception as e:
                    print(f"  Warning: Could not add rpath {rpath}: {e}")
            
            print(f"  ✓ Updated rpaths for {lib.name}")
    
    # Also fix the main executable
    exe_path = app_path / 'Contents/MacOS/Universal DJ USB'
    if exe_path.exists():
        print(f"Fixing rpath for main executable")
        rpaths_to_add = [
            '@executable_path/../Frameworks/PySide6/Qt/lib',
            '@executable_path/../Frameworks',
        ]
        
        for rpath in rpaths_to_add:
            try:
                subprocess.run(
                    ['install_name_tool', '-add_rpath', rpath, str(exe_path)],
                    check=False,
                    capture_output=True
                )
            except Exception as e:
                print(f"  Warning: Could not add rpath {rpath}: {e}")
        
        print(f"  ✓ Updated rpaths for main executable")
    
    print("=" * 50)
    
except Exception as e:
    print(f"Warning: Could not fix @rpath: {e}")
    print("The runtime hook will handle this instead.")
    print("=" * 50)
