# PyInstaller runtime hook for PySide6 on the legacy macOS app bundle.
#
# Keeps Qt library paths visible to dyld on macOS 10.14, where the packaged
# @rpath layout can otherwise fail to resolve libpyside6's Qt dependencies.
# The primary fix is the PySide6 6.3.2 pin; this hook is a fallback.

import os
import sys

if sys.platform == 'darwin' and getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS

    qt_lib_paths = [
        os.path.join(bundle_dir, 'PySide6', 'Qt', 'lib'),
        os.path.join(bundle_dir, 'PySide6', 'Qt6', 'lib'),
        os.path.join(bundle_dir, 'PySide6'),
    ]

    if bundle_dir.endswith('Contents/MacOS'):
        frameworks_dir = os.path.join(os.path.dirname(bundle_dir), 'Frameworks')
        qt_lib_paths.extend([
            os.path.join(frameworks_dir, 'PySide6', 'Qt', 'lib'),
            os.path.join(frameworks_dir, 'PySide6'),
        ])

    existing_path = os.environ.get('DYLD_LIBRARY_PATH', '')
    new_paths = [path for path in qt_lib_paths if os.path.exists(path)]

    if new_paths:
        if existing_path:
            os.environ['DYLD_LIBRARY_PATH'] = ':'.join(new_paths + [existing_path])
        else:
            os.environ['DYLD_LIBRARY_PATH'] = ':'.join(new_paths)
