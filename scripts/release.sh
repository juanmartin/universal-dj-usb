#!/bin/bash
set -euo pipefail

# Universal DJ USB - Pure Shell Release Script
# No Python execution - uses sed/awk for maximum security

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_help() {
    echo "Usage: $0 [patch|minor|major|VERSION]"
    echo ""
    echo "Arguments:"
    echo "  patch    Bump patch version (0.1.0 -> 0.1.1)"
    echo "  minor    Bump minor version (0.1.0 -> 0.2.0)"
    echo "  major    Bump major version (0.1.0 -> 1.0.0)"
    echo "  VERSION  Set specific version (e.g., 1.0.0-beta.1)"
    echo ""
    echo "Examples:"
    echo "  $0 patch     # 0.1.0 -> 0.1.1"
    echo "  $0 minor     # 0.1.0 -> 0.2.0"
    echo "  $0 1.0.0     # Set to 1.0.0"
}

# Validate version format using shell pattern matching
validate_version() {
    local version="$1"
    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?$ ]]; then
        echo -e "${RED}Error: Invalid version format: $version${NC}"
        echo "Version must match: MAJOR.MINOR.PATCH[-PRERELEASE]"
        exit 1
    fi
}

# Extract version from pyproject.toml using sed
get_current_version() {
    sed -n 's/^version = "\(.*\)"$/\1/p' pyproject.toml | head -1
}

# Update version in pyproject.toml using sed
update_version() {
    local new_version="$1"
    validate_version "$new_version"
    
    # Create backup
    cp pyproject.toml pyproject.toml.bak
    
    # Update version line
    sed -i.tmp "s/^version = \".*\"$/version = \"$new_version\"/" pyproject.toml
    rm -f pyproject.toml.tmp
    
    # Verify the change worked
    local updated_version
    updated_version=$(get_current_version)
    if [[ "$updated_version" != "$new_version" ]]; then
        echo -e "${RED}Error: Version update failed${NC}"
        mv pyproject.toml.bak pyproject.toml
        exit 1
    fi
    
    rm -f pyproject.toml.bak
    echo -e "${GREEN}Version updated to: $new_version${NC}"
}

# Bump version using shell arithmetic
bump_version() {
    local bump_type="$1"
    local current_version="$2"
    
    # Extract major.minor.patch
    local version_core
    local prerelease=""
    
    if [[ "$current_version" =~ ^([0-9]+\.[0-9]+\.[0-9]+)(-.*)?$ ]]; then
        version_core="${BASH_REMATCH[1]}"
        prerelease="${BASH_REMATCH[2]:-}"
    else
        echo -e "${RED}Error: Cannot parse version: $current_version${NC}"
        exit 1
    fi
    
    IFS='.' read -ra VERSION_PARTS <<< "$version_core"
    local major="${VERSION_PARTS[0]}"
    local minor="${VERSION_PARTS[1]}"
    local patch="${VERSION_PARTS[2]}"
    
    case "$bump_type" in
        "patch")
            patch=$((patch + 1))
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        *)
            echo -e "${RED}Error: Invalid bump type: $bump_type${NC}"
            exit 1
            ;;
    esac
    
    echo "$major.$minor.$patch"
}

if [[ $# -eq 0 ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_help
    exit 0
fi

VERSION_ARG="$1"

# Validate input
case "$VERSION_ARG" in
    "patch"|"minor"|"major")
        ;;
    *)
        validate_version "$VERSION_ARG"
        ;;
esac

# Check if we're on a clean git state
if [[ -n "$(git status --porcelain)" ]]; then
    echo -e "${RED}Error: Working directory is not clean. Please commit or stash your changes.${NC}"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(get_current_version)
if [[ -z "$CURRENT_VERSION" ]]; then
    echo -e "${RED}Error: Could not read current version from pyproject.toml${NC}"
    exit 1
fi
echo -e "${YELLOW}Current version: ${CURRENT_VERSION}${NC}"

# Calculate new version
case "$VERSION_ARG" in
    "patch"|"minor"|"major")
        echo -e "${YELLOW}Bumping ${VERSION_ARG} version...${NC}"
        NEW_VERSION=$(bump_version "$VERSION_ARG" "$CURRENT_VERSION")
        ;;
    *)
        echo -e "${YELLOW}Setting version to ${VERSION_ARG}...${NC}"
        NEW_VERSION="$VERSION_ARG"
        ;;
esac

echo -e "${GREEN}New version: ${NEW_VERSION}${NC}"

# Update version in pyproject.toml
update_version "$NEW_VERSION"

# Sync environment BEFORE committing so uv.lock is included
echo -e "${YELLOW}Syncing installed package version...${NC}"
if command -v uv >/dev/null 2>&1; then
    uv sync
else
    echo "uv not found - skipping environment sync"
fi

# Confirm with user
echo -e "${YELLOW}This will:${NC}"
echo "  1. Commit the version change and updated uv.lock"
echo "  2. Create tag v${NEW_VERSION}"
echo "  3. Push to origin with tags"
echo "  4. Trigger the build pipeline"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Aborted. Reverting version change...${NC}"
    update_version "$CURRENT_VERSION"
    # Also revert uv.lock if it exists
    if command -v uv >/dev/null 2>&1; then
        uv sync  # Restore original uv.lock
    fi
    exit 0
fi

# Commit version bump (including uv.lock)
echo -e "${YELLOW}Committing version bump...${NC}"
git add pyproject.toml
if [[ -f "uv.lock" ]]; then
    git add uv.lock
fi
git commit -m "Bump version to ${NEW_VERSION}"

# Create and push tag
echo -e "${YELLOW}Creating tag v${NEW_VERSION}...${NC}"
git tag "v${NEW_VERSION}"

echo -e "${YELLOW}Pushing to origin...${NC}"
git push origin "$(git branch --show-current)" --tags

echo -e "${GREEN}✓ Release v${NEW_VERSION} created successfully!${NC}"
echo -e "${GREEN}✓ Build pipeline will start automatically.${NC}"
echo ""
echo "Monitor the build progress at:"
echo "https://github.com/juanmartin/universal-dj-usb/actions"
