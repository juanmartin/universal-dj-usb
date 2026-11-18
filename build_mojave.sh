#!/bin/bash
set -euo pipefail

# Universal DJ USB - legacy macOS 10.14 (Mojave) GUI build.
#
# Run this on an Intel Mac running macOS 10.14 with Python 3.10 installed.
# The modern build (build.sh) keeps using the current PySide6 and is unchanged.
#
# Usage:
#   ./build_mojave.sh
#
# Optional:
#   PYTHON=/path/to/python3.10 ./build_mojave.sh

APP_NAME="Universal DJ USB"
VENV_DIR=".venv-mojave"
PYTHON="${PYTHON:-python3.10}"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "ERROR: this script only builds macOS applications." >&2
    exit 1
fi

if [[ "$(uname -m)" != "x86_64" ]]; then
    echo "ERROR: the Mojave build must run on an Intel Mac (x86_64)." >&2
    echo "Mojave does not run on Apple Silicon, and cross-built arm64 binaries cannot run there." >&2
    exit 1
fi

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "ERROR: Python 3.10 was not found as '$PYTHON'." >&2
    echo "Install it from https://www.python.org/downloads/macos/ (macOS 64-bit installer)." >&2
    exit 1
fi

"$PYTHON" - <<'PY'
import sys

if sys.version_info[:2] != (3, 10):
    raise SystemExit(
        f"ERROR: Python 3.10 is required, found {sys.version.split()[0]}. "
        "PySide6 6.3.2 does not support Python 3.11+."
    )
PY

OS_VERSION="$(sw_vers -productVersion)"
if [[ "$OS_VERSION" != 10.14* ]]; then
    echo "NOTE: building on macOS $OS_VERSION. The artifact is only validated on 10.14;"
    echo "      dependencies compiled from source may raise the minimum OS."
fi

VERSION="$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -n 1)"
if [[ -z "$VERSION" ]]; then
    echo "ERROR: could not read the version from pyproject.toml." >&2
    exit 1
fi

echo "Universal DJ USB - Mojave build"
echo "Version: $VERSION"
echo "Python:  $("$PYTHON" -V 2>&1)"
echo

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating $VENV_DIR..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

echo "Installing legacy dependencies..."
python -m pip install --no-cache-dir -r requirements-mojave.txt

# The project metadata declares Python >=3.11. The legacy environment is
# Python 3.10, so bypass the metadata check; dependencies are pinned above.
echo "Installing the project metadata..."
python -m pip install --no-cache-dir --no-deps --ignore-requires-python .

echo "Building the application..."
python -m PyInstaller udj_gui_macos_legacy.spec --clean --noconfirm

APP_PATH="dist/$APP_NAME.app"
if [[ ! -d "$APP_PATH" ]]; then
    echo "ERROR: $APP_PATH was not created." >&2
    exit 1
fi

# PySide6 6.3.2's hook collects every Qt framework. Drop the large modules the
# GUI never imports; QtQml/QtQuick/QtNetwork/QtOpenGL stay because it needs them.
echo "Trimming unused Qt frameworks..."
QT_LIB="$APP_PATH/Contents/Frameworks/PySide6/Qt/lib"
if [[ -d "$QT_LIB" ]]; then
    for pattern in \
        'QtWebEngine*.framework' \
        'Qt3D*.framework' \
        'QtCharts*.framework' \
        'QtDataVisualization*.framework' \
        'QtMultimedia*.framework' \
        'QtBluetooth.framework' \
        'QtPositioning*.framework' \
        'QtSensors*.framework' \
        'QtVirtualKeyboard*.framework' \
        'QtPdf*.framework' \
        'QtSvg*.framework'
    do
        find "$QT_LIB" -maxdepth 1 -name "$pattern" -exec rm -rf {} +
    done

    if command -v codesign >/dev/null 2>&1; then
        codesign --force --deep --sign - "$APP_PATH" >/dev/null 2>&1 || \
            echo "WARNING: ad-hoc re-signing failed; the app may still run unsigned." >&2
    fi
fi

check_minos() {
    local binary="$1"
    local label="$2"
    local minos

    if ! command -v vtool >/dev/null 2>&1; then
        return
    fi

    minos="$(vtool -arch x86_64 -show-build "$binary" 2>/dev/null | awk '
        /minos/ { print $2; exit }
        /cmd LC_VERSION_MIN_MACOSX/ { legacy = 1; next }
        legacy && /version/ { print $2; exit }
    ')"
    if [[ -z "$minos" ]]; then
        echo "WARNING: could not read the minimum OS for $label." >&2
        return
    fi

    echo "$label minimum macOS: $minos"
    case "$minos" in
        10.9|10.10|10.11|10.12|10.13|10.14) ;;
        *)
            echo "ERROR: $label requires macOS $minos, not 10.14." >&2
            exit 1
            ;;
    esac
}

echo
echo "Checking deployment targets..."
check_minos "$APP_PATH/Contents/MacOS/$APP_NAME" "main executable"
QTCORE="$(find "$APP_PATH/Contents" -path '*QtCore.framework/Versions/A/QtCore' -print -quit)"
if [[ -n "$QTCORE" ]]; then
    check_minos "$QTCORE" "QtCore"
else
    echo "WARNING: QtCore was not found in the bundle." >&2
fi
PYSIDE_LIB="$(find "$APP_PATH/Contents" -name 'libpyside6*.dylib' -print -quit)"
if [[ -n "$PYSIDE_LIB" ]]; then
    check_minos "$PYSIDE_LIB" "libpyside6"
fi
PYTHON_FRAMEWORK="$(find "$APP_PATH/Contents" -path '*Python.framework/Versions/*/Python' -print -quit)"
if [[ -n "$PYTHON_FRAMEWORK" ]]; then
    check_minos "$PYTHON_FRAMEWORK" "Python framework"
else
    echo "WARNING: the Python framework was not found in the bundle." >&2
fi

DMG_NAME="Universal-DJ-USB-${VERSION}-darwin-mojave-x64.dmg"
STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGING_DIR"' EXIT

mkdir -p "$STAGING_DIR"
cp -R "$APP_PATH" "$STAGING_DIR/"
ln -s /Applications "$STAGING_DIR/Applications"

echo
echo "Creating $DMG_NAME..."
hdiutil create \
    -volname "Universal DJ USB $VERSION" \
    -srcfolder "$STAGING_DIR" \
    -ov -format UDZO \
    "dist/$DMG_NAME" >/dev/null

echo
echo "Built: dist/$DMG_NAME"
echo "Open the app on the Mojave Mac and test a conversion before publishing."
