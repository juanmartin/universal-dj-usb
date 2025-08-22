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
CURRENT_VERSION=$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
echo -e "${YELLOW}Current version: ${CURRENT_VERSION}${NC}"

# Function to update version in pyproject.toml
update_version() {
    local new_version="$1"
    uv run python -c "
import tomllib
import tomli_w

with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)

data['project']['version'] = '$new_version'

with open('pyproject.toml', 'wb') as f:
    tomli_w.dump(data, f)
"
}

# Bump version
case "$VERSION_ARG" in
    "patch"|"minor"|"major")
        echo -e "${YELLOW}Bumping ${VERSION_ARG} version...${NC}"
        # For semantic version bumping, we need to implement version parsing
        NEW_VERSION=$(uv run python -c "
import tomllib
from packaging.version import Version

with open('pyproject.toml', 'rb') as f:
    current = tomllib.load(f)['project']['version']

v = Version(current)
if '$VERSION_ARG' == 'patch':
    new_v = f'{v.major}.{v.minor}.{v.micro + 1}'
elif '$VERSION_ARG' == 'minor':
    new_v = f'{v.major}.{v.minor + 1}.0'
elif '$VERSION_ARG' == 'major':
    new_v = f'{v.major + 1}.0.0'
print(new_v)
")
        update_version "$NEW_VERSION"
        ;;
    *)
        echo -e "${YELLOW}Setting version to ${VERSION_ARG}...${NC}"
        NEW_VERSION="$VERSION_ARG"
        update_version "$NEW_VERSION"
        ;;
esac
# Get new version (in case it was calculated)
NEW_VERSION=$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
echo -e "${GREEN}New version: ${NEW_VERSION}${NC}"

# Reinstall to sync the installed metadata with the new version
echo -e "${YELLOW}Syncing installed package version...${NC}"
uv sync

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
    update_version "$CURRENT_VERSION"
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
