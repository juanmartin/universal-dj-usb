#!/usr/bin/env python3
"""Debug script to test rekordcrate integration and understand the PDB format."""

import subprocess
import sys
import os
import traceback
from pathlib import Path

# Add the project to the Python path
sys.path.insert(0, "/Users/juanmartin/REPOS/universal-dj-usb/src")

from universal_dj_usb.rekordbox_parser import RekordboxParser


def test_rekordcrate_commands():
    """Test various rekordcrate commands."""
    print("=== TESTING REKORDCRATE COMMANDS ===")

    # Add cargo bin to PATH
    env = os.environ.copy()
    cargo_bin = os.path.expanduser("~/.cargo/bin")
    if cargo_bin not in env.get("PATH", ""):
        env["PATH"] = f"{env.get('PATH', '')}:{cargo_bin}"

    pdb_path = "/Volumes/JMSM_SANDIS/PIONEER/rekordbox/export.pdb"

    # Test list-playlists command
    print("\n1. Testing list-playlists command:")
    try:
        result = subprocess.run(
            ["rekordcrate", "list-playlists", pdb_path],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
            env=env,
        )
        lines = result.stdout.strip().split("\n")
        print(f"   ✓ Found {len(lines)} playlists")
        print("   First few playlists:")
        for i, line in enumerate(lines[:5]):
            print(f"     {i+1}. {line}")
        playlist_output = result.stdout
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        playlist_output = None

    # Test dump-pdb command
    print("\n2. Testing dump-pdb command:")
    try:
        result = subprocess.run(
            ["rekordcrate", "dump-pdb", pdb_path],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
            env=env,
        )
        print(f"   ✓ Success! Output length: {len(result.stdout)} characters")
        print("   First few lines:")
        for i, line in enumerate(result.stdout.strip().split("\n")[:5]):
            print(f"     {i+1}. {line[:100]}...")
        dump_output = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"   ✗ Failed with exit code {e.returncode}")
        print(f"     stderr: {e.stderr}")
        if e.stdout:
            print(f"     stdout preview: {e.stdout[:200]}...")
        dump_output = None
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        dump_output = None

    return playlist_output, dump_output


def analyze_pdb_structure():
    """Analyze the PDB file structure using what we learned from rekordcrate source."""
    print("\n=== ANALYZING PDB STRUCTURE ===")

    pdb_path = "/Volumes/JMSM_SANDIS/PIONEER/rekordbox/export.pdb"

    try:
        # Get file size
        file_size = os.path.getsize(pdb_path)
        print(f"PDB file size: {file_size:,} bytes ({file_size / (1024*1024):.1f} MB)")

        # Read the first few bytes to understand the header
        with open(pdb_path, "rb") as f:
            header_bytes = f.read(64)
            print(f"Header preview (first 64 bytes): {header_bytes.hex()}")

            # According to rekordcrate source, the header structure is:
            # - 4 bytes: unknown1 (should be 0)
            # - 4 bytes: page_size
            # - 4 bytes: num_tables
            # - 4 bytes: next_unused_page
            # - 4 bytes: unknown
            # - 4 bytes: sequence
            # - 4 bytes: gap (should be 0)

            import struct

            (
                unknown1,
                page_size,
                num_tables,
                next_unused_page,
                unknown,
                sequence,
                gap,
            ) = struct.unpack("<7I", header_bytes[:28])

            print(f"Header analysis:")
            print(f"  unknown1: {unknown1}")
            print(f"  page_size: {page_size}")
            print(f"  num_tables: {num_tables}")
            print(f"  next_unused_page: {next_unused_page}")
            print(f"  unknown: {unknown}")
            print(f"  sequence: {sequence}")
            print(f"  gap: {gap}")

    except Exception as e:
        print(f"Error analyzing PDB structure: {e}")
        traceback.print_exc()


def test_our_parser():
    """Test our parser implementation."""
    print("\n=== TESTING OUR PARSER ===")

    try:
        usb_path = Path("/Volumes/JMSM_SANDIS")
        parser = RekordboxParser(usb_path)

        print("\n1. Testing playlist tree parsing:")
        playlist_tree_data = parser._get_playlist_tree_rekordcrate()
        print(f"   ✓ Parsed {len(playlist_tree_data)} playlists")

        print("   Sample playlists:")
        for i, playlist in enumerate(playlist_tree_data[:5]):
            print(
                f"     {i+1}. '{playlist['name']}' (folder: {playlist['is_folder']}, id: {playlist['id']})"
            )

        print("\n2. Testing full playlist tree building:")
        playlist_tree = parser.parse_playlists()
        print(
            f"   ✓ Built playlist tree with {len(playlist_tree.all_playlists)} playlists"
        )

        print("\n3. Testing specific playlist retrieval:")
        set_playlist = parser.get_playlist_by_name("SET")
        if set_playlist:
            print(f"   ✓ Found 'SET' playlist:")
            print(f"     - ID: {set_playlist.id}")
            print(f"     - Tracks: {len(set_playlist.tracks)}")
            print(f"     - Is folder: {set_playlist.is_folder}")
            if set_playlist.tracks:
                print("     - Sample tracks:")
                for i, track in enumerate(set_playlist.tracks[:3]):
                    print(
                        f"       {i+1}. {track.title} - {track.artist} ({track.file_path.name})"
                    )
        else:
            print("   ✗ 'SET' playlist not found")

        return playlist_tree_data, set_playlist

    except Exception as e:
        print(f"   ✗ Parser failed: {e}")
        traceback.print_exc()
        return None, None


def suggest_improvements():
    """Suggest improvements based on the rekordcrate source analysis."""
    print("\n=== IMPROVEMENT SUGGESTIONS ===")

    print("Based on the rekordcrate source code analysis:")
    print("1. PDB Structure:")
    print(
        "   - PDB files contain multiple tables (tracks, playlists, playlist entries, etc.)"
    )
    print("   - Each table is a linked list of pages")
    print("   - PlaylistEntries table links tracks to playlists")
    print("   - This explains why we need both playlist structure AND playlist entries")

    print("\n2. Why dump-pdb might fail:")
    print("   - The PDB format is complex with binary data")
    print("   - Different Rekordbox versions might use slightly different formats")
    print("   - The dump command tries to parse ALL tables, not just playlists")

    print("\n3. Better approach:")
    print("   - Use list-playlists for playlist structure (this works!)")
    print("   - Implement direct PDB parsing for playlist entries")
    print("   - Use file system scanning as fallback for track metadata")
    print("   - Focus on the essential data: playlist -> track relationships")

    print("\n4. Hybrid solution:")
    print("   - Get playlist names from rekordcrate (working)")
    print("   - Scan music files for track metadata (reliable)")
    print("   - Use folder structure to infer playlist-track relationships")
    print("   - Generate NML with available data")


if __name__ == "__main__":
    # Run all tests
    playlist_output, dump_output = test_rekordcrate_commands()
    analyze_pdb_structure()
    parsed_data, set_playlist = test_our_parser()
    suggest_improvements()

    print(f"\n=== SUMMARY ===")
    if playlist_output:
        raw_count = len(playlist_output.strip().split("\n"))
        print(f"✓ Rekordcrate found {raw_count} playlists")
    else:
        print("✗ Rekordcrate playlist parsing failed")

    if parsed_data:
        print(f"✓ Our parser processed {len(parsed_data)} playlists")
    else:
        print("✗ Our parser failed")

    if dump_output:
        print("✓ dump-pdb command worked")
    else:
        print(
            "✗ dump-pdb command failed (expected - this explains the track data issue)"
        )

    if set_playlist:
        print(f"✓ Found 'SET' playlist with {len(set_playlist.tracks)} tracks")
    else:
        print("✗ Could not retrieve 'SET' playlist data")
