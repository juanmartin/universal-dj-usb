"""Traktor NML playlist generator."""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import Optional
from datetime import datetime

from .base import BaseGenerator
from ..models import Playlist, Track, CuePoint, ConversionResult


class NMLGenerator(BaseGenerator):
    """Generator for Traktor NML playlist format."""

    @property
    def file_extension(self) -> str:
        """Return the file extension for NML format."""
        return ".nml"

    def generate(
        self, playlist: Playlist, output_path: Path, usb_path: Path = None
    ) -> ConversionResult:
        """Generate a Traktor NML playlist file."""
        try:
            # Use the output_path directly as provided by the caller
            output_file = output_path

            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Extract volume name from USB path
            volume_name = ""
            if usb_path:
                volume_name = usb_path.name

            # Create NML structure
            nml_root = ET.Element("NML", VERSION="19")

            # Add header
            head = ET.SubElement(
                nml_root,
                "HEAD",
                COMPANY="www.native-instruments.com",
                PROGRAM="Traktor",
            )

            # Add empty MUSICFOLDERS section
            musicfolders = ET.SubElement(nml_root, "MUSICFOLDERS")

            # Add collection with all tracks
            collection = ET.SubElement(
                nml_root, "COLLECTION", ENTRIES=str(len(playlist.tracks))
            )

            warnings = []

            # Add all tracks to collection
            for track in playlist.tracks:
                self._add_track_to_collection(
                    collection, track, output_path, warnings, volume_name, usb_path
                )

            # Add empty SETS section
            sets = ET.SubElement(nml_root, "SETS", ENTRIES="0")

            # Add playlists section with proper structure
            playlists = ET.SubElement(nml_root, "PLAYLISTS")

            # Create root folder node
            root_node = ET.SubElement(playlists, "NODE", TYPE="FOLDER", NAME="$ROOT")
            root_subnodes = ET.SubElement(root_node, "SUBNODES", COUNT="1")

            # Create playlist node
            playlist_node = ET.SubElement(
                root_subnodes, "NODE", TYPE="PLAYLIST", NAME=playlist.name
            )

            # Create playlist element with entries
            playlist_element = ET.SubElement(
                playlist_node,
                "PLAYLIST",
                ENTRIES=str(len(playlist.tracks)),
                TYPE="LIST",
                UUID=self._generate_uuid(),
            )

            # Add playlist entries with PRIMARYKEY structure
            for track in playlist.tracks:
                entry = ET.SubElement(playlist_element, "ENTRY")
                primarykey = ET.SubElement(
                    entry,
                    "PRIMARYKEY",
                    TYPE="TRACK",
                    KEY=self._generate_track_key(track, usb_path),
                )

            # Add empty INDEXING section
            indexing = ET.SubElement(nml_root, "INDEXING")

            # Format and write XML
            xml_str = ET.tostring(nml_root, encoding="unicode")
            dom = minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent="  ")

            # Fix XML declaration to match Traktor format
            pretty_xml = pretty_xml.replace(
                '<?xml version="1.0" ?>',
                '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            )

            # Fix self-closing tags to use proper closing tags
            import re

            # Convert <TAG /> to <TAG></TAG> for ALL elements that should have closing tags
            pretty_xml = re.sub(
                r"<(HEAD|MUSICFOLDERS|LOCATION|ALBUM|ARTIST|TITLE|GENRE|MODIFICATION_INFO|MUSICAL_KEY|TEMPO|CUE_V2|LOUDNESS|INFO|SETS|INDEXING|PRIMARYKEY)(\s+[^>]*?)?\s*/>",
                r"<\1\2></\1>",
                pretty_xml,
            )

            # Additional pass to catch any remaining self-closing tags
            pretty_xml = re.sub(
                r"<([A-Z_]+)(\s+[^>]+?)\s*/>",
                r"<\1\2></\1>",
                pretty_xml,
            )

            # Remove extra blank lines
            lines = [line for line in pretty_xml.split("\\n") if line.strip()]
            formatted_xml = "\\n".join(lines)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted_xml)

            return ConversionResult(
                success=True,
                playlist_name=playlist.name,
                output_file=output_file,
                track_count=len(playlist.tracks),
                warnings=warnings,
            )

        except Exception as e:
            return ConversionResult(
                success=False,
                playlist_name=playlist.name,
                error_message=f"Failed to generate NML: {str(e)}",
            )

    def _add_track_to_collection(
        self,
        collection: ET.Element,
        track: Track,
        output_path: Path,
        warnings: list,
        volume_name: str = "",
        usb_path: Path = None,
    ) -> None:
        """Add a track entry to the collection."""
        # Get file path
        if self.config.relative_paths:
            file_path = self._normalize_path(track.file_path, output_path)
        else:
            file_path = self._normalize_path(track.file_path)

        # Convert to Traktor path format
        traktor_path = self._format_traktor_path(file_path)

        # Check if file exists (only add warning for debug purposes)
        if usb_path:
            # Construct proper absolute path
            track_path_str = str(track.file_path)
            if track_path_str.startswith("/"):
                track_path_str = track_path_str[1:]  # Remove leading slash
            absolute_file_path = usb_path / track_path_str
        else:
            absolute_file_path = track.file_path

        if not absolute_file_path.exists():
            warnings.append(f"File not found: {absolute_file_path}")

        # Create entry element with title and artist as attributes
        entry_attribs = {
            "MODIFIED_DATE": "2024/1/1",
            "MODIFIED_TIME": "0",
        }

        # Add title and artist as attributes to ENTRY
        if track.title:
            entry_attribs["TITLE"] = track.title
        if track.artist:
            entry_attribs["ARTIST"] = track.artist

        entry = ET.SubElement(collection, "ENTRY", **entry_attribs)

        # Location with volume information
        location = ET.SubElement(
            entry,
            "LOCATION",
            DIR=self._get_directory_path(traktor_path),
            FILE=track.filename,
            VOLUME=volume_name,
            VOLUMEID=volume_name,
        )

        # Album
        if track.album:
            ET.SubElement(entry, "ALBUM", TITLE=track.album)

        # Info
        info_attribs = {
            "BITRATE": str(track.bitrate) if track.bitrate else "128000",
            "GENRE": track.genre or "",
            "LABEL": "",
            "COMMENT": track.comment or "",
            "RATING": str(track.rating or 0),
            "FLAGS": "12",
            "FILESIZE": str(track.file_size) if track.file_size else "0",
        }

        if track.duration:
            info_attribs["PLAYTIME"] = str(int(track.duration))
            info_attribs["PLAYTIME_FLOAT"] = f"{track.duration:.6f}"

        if track.bpm:
            info_attribs["BPM"] = f"{track.bpm:.2f}"

        if track.key:
            info_attribs["KEY"] = track.key.value

        if track.year:
            info_attribs["RELEASE_DATE"] = f"{track.year}/1/1"

        ET.SubElement(entry, "INFO", **info_attribs)

        # Tempo
        if track.bpm:
            tempo = ET.SubElement(
                entry, "TEMPO", BPM=f"{track.bpm:.2f}", BPM_QUALITY="100.000000"
            )

        # Musical key
        if track.key:
            ET.SubElement(entry, "MUSICAL_KEY", VALUE=track.key.value)

        # Cue points
        if self.config.include_cue_points and track.cue_points:
            cues = ET.SubElement(entry, "CUE_V2")
            for i, cue in enumerate(track.cue_points):
                self._add_cue_point(cues, cue, i)

    def _add_playlist_entry(
        self, subnodes: ET.Element, track: Track, index: int
    ) -> None:
        """Add a playlist entry reference."""
        ET.SubElement(subnodes, "NODE", TYPE="TRACK", KEY=f"track_{index}")

    def _add_cue_point(self, cues: ET.Element, cue: CuePoint, index: int) -> None:
        """Add a cue point to the track."""
        cue_attribs = {
            "NAME": cue.name,
            "DISPL_ORDER": str(index),
            "TYPE": "0" if cue.type == "CUE" else "4",  # 0=cue, 4=loop
            "START": f"{cue.position:.6f}",
            "LEN": f"{cue.loop_length:.6f}" if cue.loop_length else "0.000000",
            "REPEATS": "-1",
            "HOTCUE": str(index),
        }

        if cue.color:
            cue_attribs["COLOR"] = cue.color

        ET.SubElement(cues, "CUE", **cue_attribs)

    def _format_traktor_path(self, path_str: str) -> str:
        """Format a path for Traktor's NML format."""
        if not path_str:
            return ""

        # Normalize the path to ensure it starts with /
        if not path_str.startswith("/"):
            path_str = "/" + path_str

        # Split the path into parts, removing empty parts
        parts = [part for part in path_str.split("/") if part]

        # Join with /: separator and add leading /: and trailing /:
        if parts:
            return "/:" + "/:".join(parts[:-1]) + "/:"
        else:
            return ""

    def _get_directory_path(self, traktor_path: str) -> str:
        """Get the directory portion of a Traktor path."""
        if not traktor_path:
            return "/:"

        # Remove the filename part
        parts = traktor_path.split("/:")
        if len(parts) > 1:
            return "/:".join(parts[:-1]) + "/:"
        return "/:"

    def _generate_uuid(self) -> str:
        """Generate a simple UUID for playlists."""
        import uuid

        return str(uuid.uuid4()).replace("-", "").lower()

    def _generate_track_key(self, track: Track, usb_path: Path = None) -> str:
        """Generate a track key for Traktor using proper NML path formatting."""
        track_path = track.file_path

        # Ensure we have an absolute path
        if not track_path.is_absolute():
            if usb_path:
                track_path = usb_path / track_path
            else:
                track_path = track_path.resolve()

        # Extract volume name and path components
        path_parts = track_path.parts
        if len(path_parts) >= 3 and path_parts[1] == "Volumes":
            volume_name = path_parts[2]
            # Get the path relative to the volume
            relative_parts = path_parts[3:]  # Skip /, Volumes, volume_name
            if relative_parts:
                relative_path = "/:".join(relative_parts)
                return f"{volume_name}/:{relative_path}"
            else:
                return volume_name
        else:
            # Fallback: if we have a USB path, use its name as volume
            if usb_path:
                volume_name = usb_path.name
                # Convert the track path to relative path format
                file_path_str = str(track_path).replace("\\", "/")
                if file_path_str.startswith("/"):
                    file_path_str = file_path_str[1:]  # Remove leading /
                relative_path = file_path_str.replace("/", "/:")
                return f"{volume_name}/:{relative_path}"
            else:
                # Last resort fallback
                file_path_str = str(track_path).replace("\\", "/")
                return file_path_str
