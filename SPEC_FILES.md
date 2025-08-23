# PyInstaller Spec Files - Platform-Specific Architecture

## Overview

This project now uses platform-specific PyInstaller spec files to ensure optimal builds for each platform without complex conditional logic. This approach eliminates cross-platform build issues and provides better maintainability.

## File Structure

```
├── udj_gui_windows.spec    # GUI build for Windows (onefile)
├── udj_gui_macos.spec      # GUI build for macOS (onedir + app bundle)
├── udj_cli_windows.spec    # CLI build for Windows (onefile)
├── udj_cli_macos.spec      # CLI build for macOS (onedir)
├── build.ps1               # Windows build script (uses *_windows.spec files)
└── build.sh                # macOS/Linux build script (uses *_macos.spec files)
```

## Platform Differences

### Windows (onefile builds)

**Advantages:**

- Single portable executable
- Easy distribution
- No external dependencies

**Spec file characteristics:**

- `strip=False` (not available on Windows)
- All binaries and data included in EXE
- No COLLECT step needed
- Icons use `.ico` format

### macOS (onedir builds)

**Advantages:**

- Faster startup (no decompression)
- Better for app bundles
- More efficient memory usage
- Proper macOS integration

**Spec file characteristics:**

- `strip=True` (available on Unix systems)
- EXE contains only scripts, no binaries/data
- COLLECT step bundles everything
- BUNDLE wraps COLLECT into `.app`
- Icons use `.icns` format
- Includes `info_plist` for app metadata

## Build Scripts

### Windows (`build.ps1`)

- Uses `udj_gui_windows.spec` and `udj_cli_windows.spec`
- Generates single executable files
- Optimized for Windows distribution

### macOS (`build.sh`)

- Uses `udj_gui_macos.spec` and `udj_cli_macos.spec`
- GUI: Creates `.app` bundle, then DMG installer
- CLI: Creates onedir build, then tar.gz archive

## Benefits of This Approach

1. **No Conditional Logic**: Each spec file is platform-specific and simple
2. **Optimal Builds**: Each platform gets the most appropriate build type
3. **Easier Maintenance**: Platform-specific issues are isolated
4. **Better Performance**: No runtime platform detection overhead
5. **Clear Separation**: Build logic is explicit for each platform

## Migration Notes

- **Old files removed**: `udj_gui.spec` and `udj_cli.spec`
- **New files added**: Platform-specific spec files
- **Build scripts updated**: Now reference correct spec files
- **CI/CD**: Should automatically use correct spec files per platform

## Usage

### Windows

```powershell
.\build.ps1 -GUI          # Uses udj_gui_windows.spec
.\build.ps1 -CLI          # Uses udj_cli_windows.spec
.\build.ps1 -Both         # Uses both Windows spec files
```

### macOS/Linux

```bash
./build.sh --gui          # Uses udj_gui_macos.spec
./build.sh --cli          # Uses udj_cli_macos.spec
./build.sh --both         # Uses both macOS spec files
```

This architecture should resolve the macOS build issues while maintaining optimal builds for both platforms.
