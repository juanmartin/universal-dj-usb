"""Traktor NML file generator for playlist conversion."""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .models import Playlist, Track, CuePoint, ConversionConfig
from .utils import normalize_path, sanitize_filename

logger = logging.getLogger(__name__)


def _format_traktor_path(path_str: str) -> str:
    """
    Format a path for Traktor's NML format.

    Traktor uses /: as the separator between directories.

    Args:
        path_str: Standard path string with forward slashes

    Returns:
        Formatted path string for Traktor NML format
    """
    if not path_str:
        return ""

    # Normalize the path to ensure it starts with /
    if not path_str.startswith("/"):
        path_str = "/" + path_str

    # Split the path into parts, removing empty parts
    parts = [part for part in path_str.split("/") if part]

    # Join with /: separator and add leading /: and trailing /:
    if parts:
        return "/:" + "/:".join(parts) + "/:"
    else:
        return ""


def _format_traktor_file_path(path_str: str) -> str:
    """
    Format a complete file path for Traktor's NML format.

    Args:
        path_str: Standard file path string with forward slashes

    Returns:
        Formatted file path string for Traktor NML format
    """
    if not path_str:
        return ""

    # Normalize the path to ensure it starts with /
    if not path_str.startswith("/"):
        path_str = "/" + path_str

    # Split the path into parts, removing empty parts
    parts = [part for part in path_str.split("/") if part]

    # Join with /: separator and add leading /:
    if parts:
        return "/:" + "/:".join(parts)
    else:
        return ""


class TraktorNMLGenerator:
    """Generates Traktor NML files from playlist data."""

    def __init__(self, config: ConversionConfig):
        """
        Initialize the NML generator.

        Args:
            config: Conversion configuration
        """
        self.config = config

    def generate_nml(
        self, playlist: Playlist, output_path: Path, base_path: Optional[Path] = None
    ) -> bool:
        """
        Generate an NML file for a single playlist.

        Args:
            playlist: Playlist to convert
            output_path: Path to save the NML file
            base_path: Base path for relative file paths

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Generating NML for playlist: {playlist.name}")

            # Create the root NML element
            nml = ET.Element("NML", VERSION="19")

            # Add header
            self._add_header(nml)

            # Add collection (tracks)
            collection = self._create_collection(playlist.tracks, base_path)
            nml.append(collection)

            # Add empty SETS section (as seen in reference)
            sets = ET.SubElement(nml, "SETS")
            sets.set("ENTRIES", "0")

            # Add playlists section
            playlists = self._create_playlists_section(playlist, base_path)
            nml.append(playlists)

            # Add empty INDEXING section (as seen in reference)
            indexing = ET.SubElement(nml, "INDEXING")

            # Write to file
            return self._write_nml_file(nml, output_path)

        except Exception as e:
            logger.error(f"Failed to generate NML for {playlist.name}: {e}")
            return False

    def generate_multiple_nml(
        self,
        playlists: List[Playlist],
        output_dir: Path,
        base_path: Optional[Path] = None,
    ) -> List[Path]:
        """
        Generate NML files for multiple playlists.

        Args:
            playlists: List of playlists to convert
            output_dir: Directory to save NML files
            base_path: Base path for relative file paths

        Returns:
            List of successfully created NML file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        created_files = []

        for i, playlist in enumerate(playlists):
            if self.config.file_naming == "sequential":
                filename = f"{i+1:03d}_{sanitize_filename(playlist.name)}.nml"
            else:
                filename = f"{sanitize_filename(playlist.name)}.nml"

            output_path = output_dir / filename

            if self.generate_nml(playlist, output_path, base_path):
                created_files.append(output_path)

        return created_files

    def _add_header(self, nml: ET.Element) -> None:
        """Add header information to the NML."""
        head = ET.SubElement(nml, "HEAD")
        head.set("COMPANY", "www.native-instruments.com")
        head.set("PROGRAM", "Traktor")

        # Add empty MUSICFOLDERS element as seen in reference
        musicfolders = ET.SubElement(nml, "MUSICFOLDERS")

    def _create_collection(
        self, tracks: List[Track], base_path: Optional[Path] = None
    ) -> ET.Element:
        """Create the COLLECTION element with tracks from the playlist only."""
        collection = ET.Element("COLLECTION")
        collection.set("ENTRIES", str(len(tracks)))

        for track in tracks:
            entry = self._create_track_entry(track, base_path)
            collection.append(entry)

        return collection

    def _create_track_entry(
        self, track: Track, base_path: Optional[Path] = None
    ) -> ET.Element:
        """Create a single track ENTRY element."""
        entry = ET.Element("ENTRY")
        entry.set("MODIFIED_DATE", datetime.now().strftime("%Y/%m/%d"))
        # Generate a more realistic timestamp instead of "0"
        import time

        entry.set(
            "MODIFIED_TIME", str(int(time.time() % 86400))
        )  # Seconds since start of day

        # Remove AUDIO_ID completely - Traktor will generate this via audio analysis
        # Don't include fake AUDIO_ID as it may cause Traktor to reject the entry        # Add title and artist attributes to the entry element itself (as seen in reference)
        entry.set("TITLE", track.title or track.filename)
        entry.set("ARTIST", track.artist or "Unknown Artist")

        # File location
        location = ET.SubElement(entry, "LOCATION")

        # For LOCATION DIR, we always want the absolute path
        absolute_path = str(track.file_path)

        # Format the directory path for Traktor's NML format (uses /: as separator)
        dir_path = _format_traktor_path(str(Path(absolute_path).parent))
        location.set("DIR", dir_path)
        location.set("FILE", track.filename)

        # Set volume information based on USB drive
        if base_path:
            volume_name = base_path.name
            location.set("VOLUME", volume_name)
            location.set("VOLUMEID", volume_name)
        else:
            # Try to extract volume name from the track path
            path_parts = track.file_path.parts
            if len(path_parts) >= 3 and path_parts[1] == "Volumes":
                volume_name = path_parts[2]
                location.set("VOLUME", volume_name)
                location.set("VOLUMEID", volume_name)
            else:
                location.set("VOLUME", "")
                location.set("VOLUMEID", "")

        # Album - use proper structure as in reference
        album = ET.SubElement(entry, "ALBUM")
        if track.album:
            album.set("TITLE", track.album)
            # Add TRACK attribute - use track number if available, otherwise use a default
            if hasattr(track, "track_number") and track.track_number:
                album.set("TRACK", str(track.track_number))
            else:
                album.set("TRACK", "1")  # Default track number
        else:
            album.set("TITLE", "Unknown Album")
            album.set("TRACK", "1")  # Default track number

        # Add MODIFICATION_INFO as seen in reference
        modification_info = ET.SubElement(entry, "MODIFICATION_INFO")
        modification_info.set("AUTHOR_TYPE", "user")

        # Artist
        artist = ET.SubElement(entry, "ARTIST")
        artist.set("TITLE", track.artist or "Unknown Artist")

        # Title
        title = ET.SubElement(entry, "TITLE")
        title.set("TITLE", track.title or track.filename)

        # Genre
        if track.genre:
            genre = ET.SubElement(entry, "GENRE")
            genre.set("TITLE", track.genre)

        # Info (technical details)
        info = ET.SubElement(entry, "INFO")
        if track.bitrate:
            info.set("BITRATE", str(track.bitrate))
        if track.bpm:
            info.set("BPM", f"{track.bpm:.2f}")
        if track.duration:
            info.set("PLAYTIME", str(int(track.duration)))
            info.set("PLAYTIME_FLOAT", f"{track.duration:.6f}")
        if track.sample_rate:
            info.set("SAMPLERATE", str(track.sample_rate))
        if track.file_size:
            info.set("FILESIZE", str(track.file_size))
        if track.key:
            info.set("KEY", track.key.value)
        if track.year:
            info.set("RELEASE_DATE", str(track.year))
        if track.rating:
            info.set("RATING", str(track.rating))
        if track.comment:
            info.set("COMMENT", track.comment)

        # Add common attributes seen in reference files
        info.set("FLAGS", "12")  # Common flag value seen in Traktor
        info.set("IMPORT_DATE", datetime.now().strftime("%Y/%m/%d"))  # When imported

        # Musical key
        if track.key:
            musical_key = ET.SubElement(entry, "MUSICAL_KEY")
            musical_key.set("VALUE", track.key.value)

        # Cue points and loops
        if self.config.include_cue_points and track.cue_points:
            self._add_cue_points(entry, track.cue_points)

        # Tempo information
        if track.bpm:
            tempo = ET.SubElement(entry, "TEMPO")
            tempo.set("BPM", f"{track.bpm:.2f}")
            tempo.set("BPM_QUALITY", "100.000000")

        # Add LOUDNESS element (common in Traktor NML files)
        loudness = ET.SubElement(entry, "LOUDNESS")
        loudness.set("PEAK_DB", "-1.000000")  # Default placeholder values
        loudness.set("PERCEIVED_DB", "-1.000000")
        loudness.set("ANALYZED_DB", "-1.000000")

        return entry

    def _add_cue_points(self, entry: ET.Element, cue_points: List[CuePoint]) -> None:
        """Add cue points and loops to a track entry."""
        for i, cue in enumerate(cue_points):
            if cue.type == "CUE":
                cue_element = ET.SubElement(entry, "CUE_V2")
                cue_element.set("NAME", cue.name)
                cue_element.set("DISPL_ORDER", str(i))
                cue_element.set("TYPE", "0")  # 0 = Cue, 4 = Loop
                cue_element.set("START", f"{cue.position:.6f}")
                cue_element.set("LEN", "0.000000")
                cue_element.set("REPEATS", "-1")
                if cue.color:
                    # Convert color to Traktor format (needs color mapping)
                    cue_element.set("HOTCUE", self._convert_color_to_traktor(cue.color))

            elif cue.type == "LOOP" and cue.loop_length:
                if self.config.include_loops:
                    loop_element = ET.SubElement(entry, "CUE_V2")
                    loop_element.set("NAME", cue.name)
                    loop_element.set("DISPL_ORDER", str(i))
                    loop_element.set("TYPE", "4")  # 4 = Loop
                    loop_element.set("START", f"{cue.position:.6f}")
                    loop_element.set("LEN", f"{cue.loop_length:.6f}")
                    loop_element.set("REPEATS", "-1")
                    if cue.color:
                        loop_element.set(
                            "HOTCUE", self._convert_color_to_traktor(cue.color)
                        )

    def _convert_color_to_traktor(self, color: str) -> str:
        """Convert color to Traktor hotcue format."""
        # Mapping of common colors to Traktor hotcue numbers
        color_map = {
            "red": "0",
            "orange": "1",
            "yellow": "2",
            "green": "3",
            "blue": "4",
            "purple": "5",
            "pink": "6",
            "white": "7",
        }
        return color_map.get(color.lower(), "0")

    def _create_playlists_section(
        self, playlist: Playlist, base_path: Optional[Path] = None
    ) -> ET.Element:
        """Create the PLAYLISTS section with proper folder structure."""
        playlists = ET.Element("PLAYLISTS")

        # Create the root folder node as seen in reference
        root_node = ET.SubElement(playlists, "NODE")
        root_node.set("TYPE", "FOLDER")
        root_node.set("NAME", "$ROOT")

        # Add subnodes container
        subnodes = ET.SubElement(root_node, "SUBNODES")
        subnodes.set("COUNT", "1")

        # Create a NODE for the playlist within the root folder
        node = ET.SubElement(subnodes, "NODE")
        node.set("TYPE", "PLAYLIST")
        node.set("NAME", playlist.name)

        # Add playlist
        playlist_element = ET.SubElement(node, "PLAYLIST")
        playlist_element.set("ENTRIES", str(len(playlist.tracks)))
        playlist_element.set("TYPE", "LIST")
        playlist_element.set("UUID", self._generate_uuid())

        # Add entries
        for i, track in enumerate(playlist.tracks):
            entry = ET.SubElement(playlist_element, "ENTRY")
            primarykey = ET.SubElement(entry, "PRIMARYKEY")
            primarykey.set("TYPE", "TRACK")
            primarykey.set("KEY", self._generate_track_key(track, base_path))

        return playlists

    def _generate_uuid(self) -> str:
        """Generate a simple UUID for playlists."""
        import uuid

        return str(uuid.uuid4()).replace("-", "").lower()

    def _generate_track_key(
        self, track: Track, base_path: Optional[Path] = None
    ) -> str:
        """Generate a track key for Traktor using proper NML path formatting."""
        # Get the absolute path of the track file (should be on the USB drive)
        track_path = track.file_path

        # Ensure we have an absolute path
        if not track_path.is_absolute():
            if base_path:
                track_path = base_path / track_path
            else:
                track_path = track_path.resolve()

        # Convert to string and normalize slashes
        file_path_str = str(track_path).replace("\\", "/")

        # Format the full path for Traktor's NML format (uses /: as separator)
        # This should give us the complete key like /:Volumes/:JMSM_SANDIS/:Contents/:...
        formatted_path = _format_traktor_file_path(file_path_str)

        return formatted_path

    def _write_nml_file(self, nml: ET.Element, output_path: Path) -> bool:
        """Write the NML element to a file with proper formatting."""
        try:
            # Convert to string with proper formatting
            rough_string = ET.tostring(nml, encoding="unicode")
            reparsed = minidom.parseString(rough_string)

            # Generate pretty XML with proper declaration
            pretty_xml = reparsed.toprettyxml(indent="  ", encoding=None)

            # Replace the default XML declaration with the one matching the reference
            if pretty_xml.startswith('<?xml version="1.0" ?>'):
                pretty_xml = pretty_xml.replace(
                    '<?xml version="1.0" ?>',
                    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
                )

            # Fix self-closing tags to use proper closing tags
            import re

            # Convert <TAG /> to <TAG></TAG> for elements that should have closing tags
            # This regex handles attributes and whitespace properly
            pretty_xml = re.sub(
                r"<(ALBUM|ARTIST|TITLE|GENRE|MODIFICATION_INFO|MUSICAL_KEY|TEMPO|CUE_V2|LOUDNESS|INFO)(\s+[^>]*?)?\s*/>",
                r"<\1\2></\1>",
                pretty_xml,
            )

            # Remove extra blank lines
            lines = [line for line in pretty_xml.split("\n") if line.strip()]
            pretty_xml = "\n".join(lines)

            # Write to file
            with open(output_path, "w", encoding=self.config.encoding) as f:
                f.write(pretty_xml)

            logger.info(f"Successfully wrote NML file: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to write NML file {output_path}: {e}")
            return False


def create_nml_generator(config: ConversionConfig) -> TraktorNMLGenerator:
    """
    Factory function to create a TraktorNMLGenerator.

    Args:
        config: Conversion configuration

    Returns:
        Configured TraktorNMLGenerator instance
    """
    return TraktorNMLGenerator(config)
