import sys

sys.path.insert(0, "src")
from universal_dj_usb.advanced_pdb_parser import AdvancedPDBParser
from pathlib import Path

parser = AdvancedPDBParser(
    Path("/Volumes/JMSM_SANDIS/PIONEER/rekordbox/export.pdb"),
    Path("/Volumes/JMSM_SANDIS"),
)
tracks = parser.get_tracks_for_playlist("ESPINOSO")
print("First track file_path:", tracks[0].file_path)
print("First track file_path type:", type(tracks[0].file_path))
print("First track file_path parent:", tracks[0].file_path.parent)
print("First track file_path parent str:", str(tracks[0].file_path.parent))
