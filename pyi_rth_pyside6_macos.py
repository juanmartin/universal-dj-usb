# PyInstaller runtime hook for PySide6 on macOS app bundles
# Fixes @rpath issues for Qt libraries in .app bundles on older macOS versions

import os
import sys

# Fix library paths for macOS app bundle
if sys.platform == 'darwin' and getattr(sys, 'frozen', False):
    # We're in a PyInstaller bundle
    bundle_dir = sys._MEIPASS
    
    # Add Qt library paths to DYLD_LIBRARY_PATH
    qt_lib_paths = [
        os.path.join(bundle_dir, 'PySide6', 'Qt', 'lib'),
        os.path.join(bundle_dir, 'PySide6', 'Qt6', 'lib'),
        os.path.join(bundle_dir, 'PySide6'),
    ]
    
    # Also check if we're in an app bundle structure
    if bundle_dir.endswith('Contents/MacOS'):
        frameworks_dir = os.path.join(os.path.dirname(bundle_dir), 'Frameworks')
        qt_lib_paths.extend([
            os.path.join(frameworks_dir, 'PySide6', 'Qt', 'lib'),
            os.path.join(frameworks_dir, 'PySide6'),
        ])
    
    # Set DYLD_LIBRARY_PATH if not already set
    existing_path = os.environ.get('DYLD_LIBRARY_PATH', '')
    new_paths = [p for p in qt_lib_paths if os.path.exists(p)]
    
    if new_paths:
        if existing_path:
            os.environ['DYLD_LIBRARY_PATH'] = ':'.join(new_paths + [existing_path])
        else:
            os.environ['DYLD_LIBRARY_PATH'] = ':'.join(new_paths)
