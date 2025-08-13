#!/bin/bash
# Universal build script for all platforms - optimized for local and CI/CD

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Universal DJ USB - Cross-Platform Build${NC}"
echo "=============================================="

# Get script directory and ensure we're in project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Detect platform
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
case $ARCH in
    x86_64) ARCH="x64" ;;
    arm64|aarch64) ARCH="arm64" ;;
esac

echo -e "${BLUE}🎯 Platform: ${PLATFORM}-${ARCH}${NC}"

# Check dependencies
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}❌ Poetry not found. Please install Poetry first.${NC}"
    exit 1
fi

# Install/update dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
poetry install --with dev

# Clean previous builds
echo -e "${YELLOW}🧹 Cleaning previous builds...${NC}"
rm -rf build/ dist/

# Common PyInstaller options
COMMON_OPTS=(
    --clean
    --noconfirm
    --onefile
    --add-data "src/universal_dj_usb:universal_dj_usb"
    --paths src
    --hidden-import universal_dj_usb
    --hidden-import universal_dj_usb.models
    --hidden-import universal_dj_usb.parser
    --hidden-import universal_dj_usb.metadata_extractor
    --hidden-import universal_dj_usb.generators
    --hidden-import universal_dj_usb.generators.base
    --hidden-import universal_dj_usb.generators.nml
    --hidden-import universal_dj_usb.generators.m3u
    --hidden-import universal_dj_usb.generators.m3u8
    --hidden-import universal_dj_usb.kaitai.rekordbox_pdb
    --hidden-import click
    --hidden-import rich.console
    --hidden-import rich.table
    --hidden-import rich.progress
    --hidden-import rich.panel
    --hidden-import rich.logging
    --hidden-import lxml.etree
    --hidden-import lxml._elementpath
    --hidden-import kaitaistruct
    --hidden-import mutagen.mp3
    --hidden-import mutagen.mp4
    --hidden-import mutagen.flac
    --hidden-import mutagen.oggvorbis
    --hidden-import mutagen.id3
    --hidden-import psutil
)

# Build CLI executable
echo -e "${YELLOW}🔨 Building CLI executable...${NC}"
poetry run pyinstaller \
    "${COMMON_OPTS[@]}" \
    --console \
    --name udj \
    udj_cli.py

# GUI-specific options
GUI_OPTS=(
    "${COMMON_OPTS[@]}"
    --hidden-import PySide6.QtCore
    --hidden-import PySide6.QtWidgets
    --hidden-import PySide6.QtGui
    --hidden-import signal
)

# Build GUI executable (platform-specific)
echo -e "${YELLOW}� Building GUI executable...${NC}"
if [[ "$PLATFORM" == "darwin" ]]; then
    # macOS: Build app bundle
    poetry run pyinstaller \
        "${GUI_OPTS[@]}" \
        --windowed \
        --onedir \
        --name "Universal DJ USB" \
        --osx-bundle-identifier art.juanm.udj \
        udj_gui.py
else
    # Windows/Linux: Build standalone executable
    poetry run pyinstaller \
        "${GUI_OPTS[@]}" \
        --windowed \
        --name "Universal DJ USB" \
        udj_gui.py
fi

# Show results
echo ""
echo -e "${GREEN}✅ Build completed!${NC}"
echo -e "${BLUE}📁 Executables in dist/:${NC}"
ls -lah dist/

# Platform-specific usage info
echo ""
echo -e "${GREEN}� Ready to use!${NC}"
echo -e "${BLUE}Usage:${NC}"
echo "  CLI: ./dist/udj [command] [options]"

if [[ "$PLATFORM" == "darwin" ]]; then
    echo "  GUI: open 'dist/Universal DJ USB.app'"
else
    if [[ "$PLATFORM" == "win32" ]]; then
        echo "  GUI: ./dist/Universal DJ USB.exe"
    else
        echo "  GUI: ./dist/Universal DJ USB"
    fi
fi

# Test executables
echo ""
echo -e "${YELLOW}🧪 Testing executables...${NC}"

# Test CLI
if [[ -f "dist/udj" ]]; then
    if ./dist/udj --help >/dev/null 2>&1; then
        echo -e "${GREEN}✅ CLI executable works${NC}"
    else
        echo -e "${RED}❌ CLI executable failed${NC}"
        ./dist/udj --help || true
    fi
else
    echo -e "${RED}❌ CLI executable not found${NC}"
fi

# Test GUI (just check existence, can't test headless)
if [[ "$PLATFORM" == "darwin" ]]; then
    if [[ -d "dist/Universal DJ USB.app" ]]; then
        echo -e "${GREEN}✅ GUI app bundle created${NC}"
    else
        echo -e "${RED}❌ GUI app bundle not found${NC}"
    fi
else
    GUI_NAME="Universal DJ USB"
    [[ "$PLATFORM" == "win32" ]] && GUI_NAME="${GUI_NAME}.exe"
    
    if [[ -f "dist/$GUI_NAME" ]]; then
        echo -e "${GREEN}✅ GUI executable created${NC}"
    else
        echo -e "${RED}❌ GUI executable not found${NC}"
    fi
fi

echo ""
echo -e "${GREEN}🎯 Build complete for ${PLATFORM}-${ARCH}!${NC}"
