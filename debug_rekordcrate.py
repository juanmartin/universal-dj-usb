#!/usr/bin/env python3
"""Debug script to test rekordcrate integration."""

import subprocess
import sys
import os
from pathlib import Path

# Add the project to the Python path
sys.path.insert(0, "/Users/juanmartin/REPOS/universal-dj-usb/src")

from universal_dj_usb.rekordbox_parser import RekordboxParser


def test_rekordcrate_direct():
    """Test rekordcrate directly."""
    print("Testing rekordcrate directly...")

    # Add cargo bin to PATH
    env = os.environ.copy()
    cargo_bin = os.path.expanduser("~/.cargo/bin")
    if cargo_bin not in env.get("PATH", ""):
        env["PATH"] = f"{env.get('PATH', '')}:{cargo_bin}"

    pdb_path = "/Volumes/JMSM_SANDIS/PIONEER/rekordbox/export.pdb"

    try:
        result = subprocess.run(
            ["rekordcrate", "list-playlists", pdb_path],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
            env=env,
        )
        print(f"SUCCESS: Found {len(result.stdout.strip().split('\\n'))} playlists")
        print("First few playlists:")
        for i, line in enumerate(result.stdout.strip().split("\n")[:5]):
            print(f"  {i+1}. {line}")
        return result.stdout
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def test_parser():
    """Test our parser."""
    print("\nTesting our parser...")

    try:
        usb_path = Path("/Volumes/JMSM_SANDIS")
        parser = RekordboxParser(usb_path)

        # Test the direct method
        playlist_tree_data = parser._get_playlist_tree_rekordcrate()
        print(f"Parsed {len(playlist_tree_data)} playlists")

        # Show first few playlists
        for i, playlist in enumerate(playlist_tree_data[:5]):
            print(f"  {i+1}. {playlist['name']} (folder: {playlist['is_folder']})")

        return playlist_tree_data

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    rekordcrate_output = test_rekordcrate_direct()
    parsed_data = test_parser()

    if rekordcrate_output and parsed_data:
        print(f"\nComparison:")
        print(
            f"  Rekordcrate raw lines: {len(rekordcrate_output.strip().split('\\n'))}"
        )
        print(f"  Parsed playlists: {len(parsed_data)}")
