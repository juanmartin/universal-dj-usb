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

            # Add playlists section
            playlists = self._create_playlists_section(playlist)
            nml.append(playlists)

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
        head.set("COMPANY", "Native Instruments")
        head.set("PROGRAM", "Traktor")
        head.set("VERSION", "3.11.0")

    def _create_collection(
        self, tracks: List[Track], base_path: Optional[Path] = None
    ) -> ET.Element:
        """Create the COLLECTION element with all tracks."""
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
        entry.set("MODIFIED_TIME", "0")
        entry.set("AUDIO_ID", "INVALID")  # Traktor will generate this

        # File location
        location = ET.SubElement(entry, "LOCATION")
        file_path = normalize_path(
            track.file_path, base_path, self.config.relative_paths
        )
        location.set("DIR", f"/{Path(file_path).parent}/")
        location.set("FILE", track.filename)
        location.set("VOLUME", "")
        location.set("VOLUMEID", "")

        # Album
        if track.album:
            album = ET.SubElement(entry, "ALBUM")
            album.set("TITLE", track.album)

        # Artist
        artist = ET.SubElement(entry, "ARTIST")
        artist.set("TITLE", track.artist)

        # Title
        title = ET.SubElement(entry, "TITLE")
        title.set("TITLE", track.title)

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

    def _create_playlists_section(self, playlist: Playlist) -> ET.Element:
        """Create the PLAYLISTS section."""
        playlists = ET.Element("PLAYLISTS")

        # Create a NODE for the playlist
        node = ET.SubElement(playlists, "NODE")
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
            primarykey.set("KEY", self._generate_track_key(track))

        return playlists

    def _generate_uuid(self) -> str:
        """Generate a simple UUID for playlists."""
        import uuid

        return str(uuid.uuid4()).upper()

    def _generate_track_key(self, track: Track) -> str:
        """Generate a track key for Traktor."""
        # Use file path as the key (Traktor will map this)
        return str(track.file_path)

    def _write_nml_file(self, nml: ET.Element, output_path: Path) -> bool:
        """Write the NML element to a file with proper formatting."""
        try:
            # Convert to string with proper formatting
            rough_string = ET.tostring(nml, encoding="unicode")
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(
                indent="  ", encoding=self.config.encoding
            )

            # Remove extra blank lines
            lines = [
                line
                for line in pretty_xml.decode(self.config.encoding).split("\n")
                if line.strip()
            ]
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
