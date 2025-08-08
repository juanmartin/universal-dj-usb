#!/bin/bash
# Script to update Kaitai Struct definitions from rekordcrate submodule

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REKORDCRATE_DIR="$PROJECT_ROOT/external/rekordcrate"
KAITAI_OUTPUT_DIR="$PROJECT_ROOT/src/universal_dj_usb/pdb_parser"

echo "🔄 Updating Kaitai Struct definitions from rekordcrate..."

# Check if rekordcrate submodule exists
if [ ! -d "$REKORDCRATE_DIR" ]; then
    echo "❌ rekordcrate submodule not found at $REKORDCRATE_DIR"
    echo "Run: git submodule add https://github.com/Holzhaus/rekordcrate.git external/rekordcrate"
    exit 1
fi

# Update submodule to latest
echo "📥 Updating rekordcrate submodule..."
cd "$PROJECT_ROOT"
git submodule update --remote external/rekordcrate
cd "$REKORDCRATE_DIR"
LATEST_COMMIT=$(git rev-parse --short HEAD)
echo "✅ Updated to commit: $LATEST_COMMIT"

# Check for kaitai-struct-compiler
if ! command -v kaitai-struct-compiler &> /dev/null; then
    echo "❌ kaitai-struct-compiler not found!"
    echo "Install it with:"
    echo "  brew install kaitai-struct-compiler  # macOS"
    echo "  # or download from: https://kaitai.io/"
    exit 1
fi

# Find .ksy files in rekordcrate
KSY_FILES=$(find "$REKORDCRATE_DIR" -name "*.ksy" 2>/dev/null)

if [ -z "$KSY_FILES" ]; then
    echo "❌ No .ksy files found in rekordcrate"
    echo "Looking for Kaitai definitions in the repository..."
    # Alternative locations to check
    POSSIBLE_DIRS=(
        "$REKORDCRATE_DIR/kaitai"
        "$REKORDCRATE_DIR/formats"
        "$REKORDCRATE_DIR/spec"
        "$REKORDCRATE_DIR/src"
    )
    
    for dir in "${POSSIBLE_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            echo "Checking $dir..."
            find "$dir" -name "*.ksy" 2>/dev/null || true
        fi
    done
    
    echo "📝 Note: rekordcrate may not include .ksy files directly."
    echo "You may need to get them from the Deep Symmetry project:"
    echo "https://github.com/Deep-Symmetry/dysentery"
    exit 1
fi

# Create output directory
mkdir -p "$KAITAI_OUTPUT_DIR"

# Generate Python classes from .ksy files
echo "🔨 Generating Python classes..."
for ksy_file in $KSY_FILES; do
    filename=$(basename "$ksy_file" .ksy)
    echo "  Processing: $filename.ksy"
    
    kaitai-struct-compiler \
        --target python \
        --outdir "$KAITAI_OUTPUT_DIR" \
        "$ksy_file"
    
    echo "  ✅ Generated: ${filename}.py"
done

# Update __init__.py
echo "📝 Updating __init__.py..."
cat > "$KAITAI_OUTPUT_DIR/__init__.py" << 'EOF'
"""PDB parser module using Kaitai Struct.

Generated from rekordcrate Kaitai Struct definitions.
DO NOT EDIT MANUALLY - Use scripts/update_kaitai.sh to regenerate.
"""

# Import all generated classes
try:
    from .rekordbox_pdb import RekordboxPdb
    __all__ = ['RekordboxPdb']
except ImportError as e:
    import logging
    logging.warning(f"Failed to import Kaitai Struct classes: {e}")
    __all__ = []
EOF

# Create update info file
cat > "$KAITAI_OUTPUT_DIR/GENERATED_INFO.md" << EOF
# Generated Kaitai Struct Files

**DO NOT EDIT THESE FILES MANUALLY**

These files were generated from rekordcrate Kaitai Struct definitions.

- **Generated on**: $(date)
- **rekordcrate commit**: $LATEST_COMMIT
- **Source**: external/rekordcrate submodule

To update these files, run:
\`\`\`bash
./scripts/update_kaitai.sh
\`\`\`

## Generated Files

EOF

# List generated files
for py_file in "$KAITAI_OUTPUT_DIR"/*.py; do
    if [ "$(basename "$py_file")" != "__init__.py" ]; then
        echo "- $(basename "$py_file")" >> "$KAITAI_OUTPUT_DIR/GENERATED_INFO.md"
    fi
done

echo ""
echo "✅ Kaitai Struct definitions updated successfully!"
echo "📁 Generated files in: $KAITAI_OUTPUT_DIR"
echo "📋 See GENERATED_INFO.md for details"
echo ""
echo "Next steps:"
echo "1. Test the updated parser: python -m universal_dj_usb.cli detect"
echo "2. Run tests to ensure compatibility"
echo "3. Commit the updated definitions if working correctly"