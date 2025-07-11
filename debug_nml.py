import sys

sys.path.insert(0, "src")
from universal_dj_usb.nml_generator import TraktorNMLGenerator
from universal_dj_usb.models import ConversionConfig, Track
from pathlib import Path
import time

# Create test track
track = Track(
    title="Test Track",
    artist="Test Artist",
    album="Test Album",
    file_path=Path("/Volumes/JMSM_SANDIS/Contents/Test/test.mp3"),
)

# Create generator
config = ConversionConfig()
generator = TraktorNMLGenerator(config)

# Create track entry and check attributes
entry = generator._create_track_entry(track)
print("MODIFIED_TIME:", entry.get("MODIFIED_TIME"))
print(
    "AUDIO_ID:", entry.get("AUDIO_ID")[:50] + "..." if entry.get("AUDIO_ID") else "None"
)
print("TITLE:", entry.get("TITLE"))
print("ARTIST:", entry.get("ARTIST"))
