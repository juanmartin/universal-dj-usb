#!/usr/bin/env python3
"""Quick test script to validate the new project structure."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report success/failure."""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        print(f"  ✅ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed: {e.stderr.strip()}")
        return False


def test_project_structure():
    """Test the new project structure."""
    print("🧪 Testing new project structure...")
    print("=" * 50)

    # Test poetry configuration
    if not run_command("poetry check", "Validating pyproject.toml"):
        return False

    # Install dependencies
    if not run_command("poetry install", "Installing dependencies"):
        return False

    # Test CLI help
    if not run_command("poetry run udj --help", "Testing CLI help"):
        return False

    # Test imports
    if not run_command(
        "poetry run python -c 'import universal_dj_usb; print(\"Import successful\")'",
        "Testing imports",
    ):
        return False

    # Run basic tests
    if not run_command("poetry run pytest -v", "Running tests"):
        return False

    print("\n" + "=" * 50)
    print("✅ All tests passed! Project structure is ready.")
    print("\nYou can now use the CLI:")
    print("  poetry run udj detect /path/to/usb")
    print("  poetry run udj list-playlists /path/to/usb")
    print("  poetry run udj convert /path/to/usb -f nml")


def main():
    """Main test function."""
    if not Path("pyproject.toml").exists():
        print("❌ Run this after migration (pyproject.toml not found)")
        sys.exit(1)

    # Change to project directory
    import os

    os.chdir(Path(__file__).parent)

    test_project_structure()


if __name__ == "__main__":
    main()
