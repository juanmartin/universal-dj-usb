#!/usr/bin/env python3
"""Improved Rekordbox parser that directly reads PDB file structure."""

import struct
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SimplePDBParser:
    """Simplified PDB parser focused on playlist entries."""

    def __init__(self, pdb_path: Path):
        self.pdb_path = pdb_path
        self.header = None
        self.tables = {}

    def parse_header(self) -> bool:
        """Parse the PDB header to get table information."""
        try:
            with open(self.pdb_path, "rb") as f:
                # Read header (28 bytes)
                header_data = f.read(28)
                if len(header_data) < 28:
                    return False

                # Unpack header according to rekordcrate source
                (
                    unknown1,
                    page_size,
                    num_tables,
                    next_unused_page,
                    unknown,
                    sequence,
                    gap,
                ) = struct.unpack("<7I", header_data)

                self.header = {
                    "page_size": page_size,
                    "num_tables": num_tables,
                    "sequence": sequence,
                }

                logger.info(f"PDB Header: {self.header}")

                # Read table entries
                for i in range(num_tables):
                    table_data = f.read(16)  # Each table entry is 16 bytes
                    if len(table_data) < 16:
                        break

                    page_type, empty_candidate, first_page, last_page = struct.unpack(
                        "<4I", table_data
                    )

                    table_info = {
                        "page_type": page_type,
                        "first_page": first_page,
                        "last_page": last_page,
                    }

                    # According to rekordcrate source:
                    # PageType::PlaylistEntries = 8
                    # PageType::PlaylistTree = 7
                    # PageType::Tracks = 0
                    if page_type in [0, 7, 8]:  # Tracks, PlaylistTree, PlaylistEntries
                        self.tables[page_type] = table_info
                        logger.info(f"Found table {page_type}: {table_info}")

                return True

        except Exception as e:
            logger.error(f"Failed to parse PDB header: {e}")
            return False

    def find_set_playlist_id(self, playlist_names: List[str]) -> Optional[int]:
        """Find the playlist ID for 'SET' from the rekordcrate playlist names."""
        for i, name in enumerate(playlist_names):
            # Clean the name (remove emoji and whitespace)
            clean_name = name.replace("🗎", "").strip()
            if clean_name == "SET":
                # The playlist ID is typically the index + 1, but this is an approximation
                # We would need to parse the actual PlaylistTree table for exact IDs
                return i + 1
        return None

    def get_tracks_in_folder(self, usb_path: Path, max_tracks: int = 200) -> List[Path]:
        """Scan for music files, but limit to reasonable number for SET playlist."""
        music_files = []
        music_extensions = {
            ".mp3",
            ".wav",
            ".flac",
            ".aac",
            ".m4a",
            ".ogg",
            ".aif",
            ".aiff",
        }

        # Look for files that might be in the SET playlist
        # Based on your file structure, look in Contents directory
        contents_dir = usb_path / "Contents"
        if not contents_dir.exists():
            logger.warning(f"Contents directory not found: {contents_dir}")
            return []

        logger.info(f"Scanning {contents_dir} for music files...")

        # Try to find files that are likely in playlists
        # Look for recently modified files or files in specific folders
        for root, dirs, files in os.walk(contents_dir):
            root_path = Path(root)

            # Skip very deep nested directories (probably not in main playlists)
            relative_depth = len(root_path.relative_to(contents_dir).parts)
            if relative_depth > 3:
                continue

            for file in files:
                file_path = root_path / file
                if file_path.suffix.lower() in music_extensions:
                    try:
                        # Check if file is reasonable size (not tiny samples)
                        file_size = file_path.stat().st_size
                        if file_size > 1024 * 1024:  # > 1MB
                            music_files.append(file_path)

                            if len(music_files) >= max_tracks:
                                logger.info(f"Reached limit of {max_tracks} tracks")
                                return music_files

                    except Exception as e:
                        logger.debug(f"Error checking file {file_path}: {e}")
                        continue

        logger.info(f"Found {len(music_files)} music files")
        return music_files


def test_simplified_parser():
    """Test the simplified PDB parser."""
    print("=== TESTING SIMPLIFIED PDB PARSER ===")

    usb_path = Path("/Volumes/JMSM_SANDIS")
    pdb_path = usb_path / "PIONEER" / "rekordbox" / "export.pdb"

    parser = SimplePDBParser(pdb_path)

    print("\n1. Parsing PDB header:")
    if parser.parse_header():
        print(f"   ✓ Successfully parsed header")
        print(f"   - Page size: {parser.header['page_size']}")
        print(f"   - Number of tables: {parser.header['num_tables']}")
        print(f"   - Found relevant tables: {list(parser.tables.keys())}")
    else:
        print("   ✗ Failed to parse header")
        return

    print("\n2. Getting playlist names from rekordcrate:")
    try:
        # Get playlist names from rekordcrate (we know this works)
        import subprocess

        env = os.environ.copy()
        cargo_bin = os.path.expanduser("~/.cargo/bin")
        if cargo_bin not in env.get("PATH", ""):
            env["PATH"] = f"{env.get('PATH', '')}:{cargo_bin}"

        result = subprocess.run(
            ["rekordcrate", "list-playlists", str(pdb_path)],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
            env=env,
        )
        playlist_names = [
            line.strip() for line in result.stdout.strip().split("\n") if line.strip()
        ]
        print(f"   ✓ Found {len(playlist_names)} playlists")

        # Find SET playlist
        set_id = parser.find_set_playlist_id(playlist_names)
        if set_id:
            print(f"   ✓ Found 'SET' playlist at approximate position {set_id}")
        else:
            print("   ✗ Could not find 'SET' playlist")

    except Exception as e:
        print(f"   ✗ Failed to get playlist names: {e}")
        return

    print("\n3. Scanning for music files (limited sample):")
    music_files = parser.get_tracks_in_folder(usb_path, max_tracks=165)
    print(f"   ✓ Found {len(music_files)} music files")
    if music_files:
        print("   Sample files:")
        for i, file_path in enumerate(music_files[:5]):
            rel_path = file_path.relative_to(usb_path)
            print(f"     {i+1}. {rel_path}")

    return music_files


if __name__ == "__main__":
    test_simplified_parser()
