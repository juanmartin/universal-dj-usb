"""Universal DJ USB Playlist Converter.

A powerful, cross-platform application that converts Rekordbox prepared
USB playlists to Traktor's NML format.
"""

__version__ = "0.1.0"
__author__ = "Universal DJ USB Team"
__email__ = "info@universal-dj-usb.com"
__license__ = "MIT"

from .converter import RekordboxToTraktorConverter
from .models import Playlist, Track, CuePoint
from .utils import detect_usb_drives, normalize_path

__all__ = [
    "RekordboxToTraktorConverter",
    "Playlist",
    "Track",
    "CuePoint",
    "detect_usb_drives",
    "normalize_path",
]
