#!/bin/bash
set -euo pipefail

# Universal DJ USB - Release Script
# Automates version bumping and tag creation

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

if [[ $# -eq 0 ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_help
    exit 0
fi

VERSION_ARG="$1"

# Check if we're on a clean git state
if [[ -n "$(git status --porcelain)" ]]; then
    echo -e "${RED}Error: Working directory is not clean. Please commit or stash your changes.${NC}"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(poetry version -s)
echo -e "${YELLOW}Current version: ${CURRENT_VERSION}${NC}"

# Bump version
case "$VERSION_ARG" in
    "patch"|"minor"|"major")
        echo -e "${YELLOW}Bumping ${VERSION_ARG} version...${NC}"
        poetry version "$VERSION_ARG"
        ;;
    *)
        echo -e "${YELLOW}Setting version to ${VERSION_ARG}...${NC}"
        poetry version "$VERSION_ARG"
        ;;
esac

# Get new version
NEW_VERSION=$(poetry version -s)
echo -e "${GREEN}New version: ${NEW_VERSION}${NC}"

# Confirm with user
echo -e "${YELLOW}This will:${NC}"
echo "  1. Commit the version change"
echo "  2. Create tag v${NEW_VERSION}"
echo "  3. Push to origin with tags"
echo "  4. Trigger the build pipeline"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Aborted. Reverting version change...${NC}"
    poetry version "$CURRENT_VERSION"
    exit 0
fi

# Commit version bump
echo -e "${YELLOW}Committing version bump...${NC}"
git add pyproject.toml
git commit -m "Bump version to ${NEW_VERSION}"

# Create and push tag
echo -e "${YELLOW}Creating tag v${NEW_VERSION}...${NC}"
git tag "v${NEW_VERSION}"

echo -e "${YELLOW}Pushing to origin...${NC}"
git push origin $(git branch --show-current) --tags

echo -e "${GREEN}✓ Release v${NEW_VERSION} created successfully!${NC}"
echo -e "${GREEN}✓ Build pipeline will start automatically.${NC}"
echo ""
echo "Monitor the build progress at:"
echo "https://github.com/juanmartin/universal-dj-usb/actions"
