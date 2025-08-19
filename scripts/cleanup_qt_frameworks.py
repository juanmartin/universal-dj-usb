#!/usr/bin/env python3
"""
Post-build script to remove unnecessary Qt frameworks from macOS app bundle.
This script runs after PyInstaller finishes to reduce the final app size.
"""

import shutil
import sys
from pathlib import Path


def cleanup_qt_frameworks(app_name="Universal DJ USB"):
    """Remove unwanted Qt frameworks after the app bundle is created."""
    
    app_path = Path("dist") / f"{app_name}.app"
    qt_frameworks_path = app_path / "Contents/Frameworks/PySide6/Qt/lib"
    
    if not qt_frameworks_path.exists():
        print("Qt frameworks path not found, skipping cleanup")
        return 0, 0
    
    print(f"Cleaning up Qt frameworks in: {qt_frameworks_path}")
    
    # List available frameworks before cleanup
    available_frameworks = [f.name for f in qt_frameworks_path.glob("Qt*.framework")]
    print(f"Available Qt frameworks: {len(available_frameworks)}")
    for fw in sorted(available_frameworks):
        print(f"  - {fw}")
    
    # Frameworks we can safely remove (confirmed safe to remove)
    frameworks_to_remove = [
        "QtPdf.framework",
        "QtSvg.framework", 
        "QtVirtualKeyboard.framework",
        "QtVirtualKeyboardQml.framework",
    ]
    
    # Additional frameworks that might be safe to remove (test incrementally)
    # Uncomment one at a time to test - some may break the app!
    additional_frameworks = [
        "QtQml.framework",           # QML engine - might be used internally by Qt
        "QtQmlMeta.framework",       # QML metadata - likely safe
        "QtQmlModels.framework",     # QML models - likely safe
        "QtQmlWorkerScript.framework", # QML worker scripts - likely safe
        "QtQuick.framework",         # Quick UI framework - likely safe
        "QtNetwork.framework",       # Network access - might be needed by other components
        "QtOpenGL.framework",        # OpenGL - might be used by widgets for rendering
    ]
    
    # You can enable additional cleanup by uncommenting this line:
    frameworks_to_remove.extend(additional_frameworks)
    
    removed_count = 0
    total_size_saved = 0
    
    print(f"\nRemoving {len(frameworks_to_remove)} Qt frameworks...")
    
    for framework_name in frameworks_to_remove:
        framework_path = qt_frameworks_path / framework_name
        if framework_path.exists():
            # Calculate size before removal
            size_before = sum(f.stat().st_size for f in framework_path.rglob('*') if f.is_file())
            total_size_saved += size_before
            
            print(f"  Removing {framework_name} ({size_before / 1024 / 1024:.1f} MB)")
            shutil.rmtree(framework_path)
            removed_count += 1
        else:
            print(f"  {framework_name} not found (already excluded)")
    
    # Show remaining frameworks
    remaining_frameworks = [f.name for f in qt_frameworks_path.glob("Qt*.framework")]
    print(f"\nRemaining Qt frameworks: {len(remaining_frameworks)}")
    for fw in sorted(remaining_frameworks):
        print(f"  - {fw}")
    
    print(f"\nCleanup complete:")
    print(f"  - Removed {removed_count} Qt frameworks")
    print(f"  - Saved {total_size_saved / 1024 / 1024:.1f} MB")
    print(f"  - {len(remaining_frameworks)} frameworks remaining")
    
    return removed_count, total_size_saved


def main():
    """Main entry point for the cleanup script."""
    app_name = sys.argv[1] if len(sys.argv) > 1 else "Universal DJ USB"
    
    print("=== Qt Framework Cleanup ===")
    try:
        removed, saved = cleanup_qt_frameworks(app_name)
        print("=== Cleanup Complete ===\n")
        return 0
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
