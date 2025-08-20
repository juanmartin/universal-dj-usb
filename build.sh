#!/bin/bash
set -euo pipefail

# Universal DJ USB - Build Script
# Uses spec files for customization, keeping this script simple and maintainable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Build configuration
VERSION=$(poetry version -s)
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

# Normalize architecture names
case "$ARCH" in
    "arm64") ARCH_SUFFIX="arm64" ;;
    "x86_64") ARCH_SUFFIX="x64" ;;
    *) ARCH_SUFFIX="$ARCH" ;;
esac

print_header() {
    echo -e "${GREEN}"
    echo "Universal DJ USB - Build Script"
    echo "==============================="
    echo -e "${NC}"
    echo "Version: $VERSION"
    echo "Platform: $PLATFORM-$ARCH_SUFFIX"
    echo ""
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --gui          Build GUI application (default)"
    echo "  --cli          Build CLI application"
    echo "  --both         Build both GUI and CLI"
    echo "  --clean        Clean build artifacts before building"
    echo "  --skip-tests   Skip running tests"
    echo "  --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Build GUI with default settings"
    echo "  $0 --cli             # Build CLI only"
    echo "  $0 --both --clean    # Clean build both applications"
}

clean_build() {
    echo -e "${YELLOW}Cleaning build artifacts...${NC}"
    rm -rf build/ dist/
    echo "✓ Build artifacts cleaned"
    echo ""
}

install_dependencies() {
    echo -e "${YELLOW}Installing dependencies...${NC}"
    # Install runtime dependencies and build tools
    poetry install --with dev
    echo "✓ Dependencies installed"
    echo ""
}

build_gui() {
    echo -e "${YELLOW}Building GUI application...${NC}"
    poetry run pyinstaller udj_gui.spec --clean --noconfirm
    
    # Cleanup Qt frameworks to reduce size
    if [[ -f "scripts/cleanup_qt_frameworks.py" ]]; then
        echo -e "${YELLOW}Cleaning up Qt frameworks...${NC}"
        python3 scripts/cleanup_qt_frameworks.py "Universal DJ USB"
    fi
    
    if [[ "$PLATFORM" == "darwin" ]]; then
        echo -e "${YELLOW}Creating DMG installer...${NC}"
        create_dmg_gui
    fi
    
    echo "✓ GUI build completed"
}

build_cli() {
    echo -e "${YELLOW}Building CLI application...${NC}"
    poetry run pyinstaller udj_cli.spec --clean --noconfirm
    
    if [[ "$PLATFORM" == "darwin" ]]; then
        echo -e "${YELLOW}Creating CLI archive...${NC}"
        create_archive_cli
    fi
    
    echo "✓ CLI build completed"
}

create_dmg_gui() {
    # Determine appropriate naming based on context
    local dmg_name
    if [[ "${CI:-}" == "true" ]]; then
        # CI build: use the BUILD_ID from GitHub Actions environment
        local build_id="${BUILD_ID:-$VERSION}"
        dmg_name="Universal-DJ-USB-${build_id}-${PLATFORM}-${ARCH_SUFFIX}.dmg"
    else
        # Local build: include version
        dmg_name="Universal-DJ-USB-${VERSION}-${ARCH_SUFFIX}.dmg"
    fi
    
    # Create temporary DMG directory structure
    local temp_dmg_dir=$(mktemp -d)
    local dmg_contents="$temp_dmg_dir/dmg_contents"
    mkdir -p "$dmg_contents"
    
    # Copy the app bundle
    cp -R "dist/Universal DJ USB.app" "$dmg_contents/"
    
    # Create symbolic link to Applications folder
    ln -s /Applications "$dmg_contents/Applications"
    
    # Create DMG with proper layout
    hdiutil create -volname "Universal DJ USB $VERSION" \
        -srcfolder "$dmg_contents" \
        -ov -format UDZO \
        "dist/$dmg_name"
    
    # Cleanup
    rm -rf "$temp_dmg_dir"
    
    echo "✓ DMG created: $dmg_name"
}

create_archive_cli() {
    local archive_name="udj-cli-${VERSION}-${ARCH_SUFFIX}.tar.gz"
    
    cd dist
    tar -czf "$archive_name" udj
    cd ..
    
    echo "✓ CLI archive created: $archive_name"
}

run_tests() {
    echo -e "${YELLOW}Running tests...${NC}"
    poetry run pytest --tb=short
    echo "✓ Tests passed"
    echo ""
}

show_results() {
    echo -e "${GREEN}"
    echo "Build Results"
    echo "============="
    echo -e "${NC}"
    
    if [[ -d "dist" ]]; then
        echo "Built files:"
        for file in dist/*; do
            if [[ -f "$file" ]]; then
                size=$(du -sh "$file" | cut -f1)
                echo "  $(basename "$file"): $size"
            elif [[ -d "$file" ]]; then
                size=$(du -sh "$file" | cut -f1)  
                echo "  $(basename "$file"): $size"
            fi
        done
    else
        echo "No build artifacts found."
    fi
    echo ""
}

# Parse command line arguments
BUILD_GUI=false
BUILD_CLI=false
CLEAN_BUILD=false
SKIP_TESTS=false

if [[ $# -eq 0 ]]; then
    BUILD_GUI=true  # Default to GUI if no arguments
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --gui)
            BUILD_GUI=true
            shift
            ;;
        --cli)
            BUILD_CLI=true
            shift
            ;;
        --both)
            BUILD_GUI=true
            BUILD_CLI=true
            shift
            ;;
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Main build process
print_header

if [[ "$CLEAN_BUILD" == "true" ]]; then
    clean_build
fi

install_dependencies

if [[ "$SKIP_TESTS" == "false" ]]; then
    run_tests
fi

if [[ "$BUILD_GUI" == "true" ]]; then
    build_gui
    echo ""
fi

if [[ "$BUILD_CLI" == "true" ]]; then
    build_cli  
    echo ""
fi

show_results

echo -e "${GREEN}✓ Build completed successfully!${NC}"
