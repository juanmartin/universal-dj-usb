#!/usr/bin/env python3

from src.universal_dj_usb.advanced_pdb_parser import AdvancedPDBParser
from pathlib import Path

parser = AdvancedPDBParser(
    Path("/Volumes/JMSM_SANDIS/PIONEER/rekordbox/export.pdb"),
    Path("/Volumes/JMSM_SANDIS"),
)
tracks = parser.get_tracks_for_playlist("ESPINOSO")

print(f"Found {len(tracks)} tracks for ESPINOSO")
print("\nFirst 3 tracks:")
for i, track in enumerate(tracks[:3]):
    print(f"{i+1}. {track.title}")
    print(f"   Path: {track.file_path}")
    print(f"   Absolute: {track.file_path.is_absolute()}")
    print()
