"""Universal DJ USB Playlist Converter.

A tool for converting Rekordbox USB playlists to various formats including
Traktor NML, M3U, and M3U8.
"""

def _get_version() -> str:
    """Get version from pyproject.toml as source of truth, fallback to installed metadata."""
    try:
        # First try: parse pyproject.toml directly (source of truth in development)
        from pathlib import Path
        import re
        
        # Look for pyproject.toml starting from this package directory
        current_dir = Path(__file__).resolve().parent
        for parent in [current_dir] + list(current_dir.parents):
            pyproject_file = parent / "pyproject.toml"
            if pyproject_file.exists():
                text = pyproject_file.read_text(encoding="utf-8")
                
                # Try modern tomllib (Python 3.11+)
                try:
                    import tomllib
                    data = tomllib.loads(text)
                    return data["tool"]["poetry"]["version"]
                except (ImportError, KeyError):
                    pass
                
                # Try third-party toml library
                try:
                    import toml
                    data = toml.loads(text)
                    return data["tool"]["poetry"]["version"]
                except (ImportError, KeyError):
                    pass
                
                # Regex fallback for simple cases
                match = re.search(
                    r'^\s*version\s*=\s*["\']([^"\']+)["\']', 
                    text, 
                    re.MULTILINE
                )
                if match:
                    return match.group(1)
                break
    except Exception:
        pass
    
    try:
        # Fallback: installed package metadata (when distributed/installed elsewhere)
        from importlib import metadata
        return metadata.version("universal-dj-usb")
    except Exception:
        pass
    
    return "0.0.0"  # Ultimate fallback

__version__ = _get_version()
__author__ = "Juan Martin"
__email__ = "juanmartinsesali@gmail.com"

from .models import Track, Playlist, PlaylistTree
from .parser import RekordboxParser

__all__ = ["Track", "Playlist", "PlaylistTree", "RekordboxParser"]
