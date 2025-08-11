"""Audio metadata extraction using ID3 tags and file path parsing."""

import logging
import re
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

try:
    from mutagen import File
    from mutagen.id3 import ID3NoHeaderError

    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

logger = logging.getLogger(__name__)


class AudioMetadataExtractor:
    """Extract metadata from audio files using ID3 tags and file path analysis."""

    @staticmethod
    def extract_metadata_from_file(file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from an audio file using ID3 tags.

        Args:
            file_path: Path to the audio file

        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {}

        if not MUTAGEN_AVAILABLE:
            logger.debug("Mutagen not available, skipping ID3 tag extraction")
            return metadata

        if not file_path.exists():
            logger.debug(f"File does not exist: {file_path}")
            return metadata

        try:
            audio_file = File(file_path)
            if audio_file is None:
                logger.debug(f"Could not read audio file: {file_path}")
                return metadata

            # Extract basic metadata
            if hasattr(audio_file, "info") and audio_file.info:
                info = audio_file.info

                # Duration in seconds
                if hasattr(info, "length") and info.length:
                    metadata["duration"] = float(info.length)

                # Bitrate in bps (already in correct format for Traktor)
                if hasattr(info, "bitrate") and info.bitrate:
                    metadata["bitrate"] = int(info.bitrate)

                # Sample rate
                if hasattr(info, "sample_rate") and info.sample_rate:
                    metadata["sample_rate"] = int(info.sample_rate)

            # Extract ID3 tags if available
            if hasattr(audio_file, "tags") and audio_file.tags:
                tags = audio_file.tags

                # Title
                if "TIT2" in tags:  # ID3v2 title
                    metadata["title"] = str(tags["TIT2"][0])
                elif "TITLE" in tags:  # Vorbis comment
                    metadata["title"] = str(tags["TITLE"][0])

                # Artist
                if "TPE1" in tags:  # ID3v2 artist
                    metadata["artist"] = str(tags["TPE1"][0])
                elif "ARTIST" in tags:  # Vorbis comment
                    metadata["artist"] = str(tags["ARTIST"][0])

                # Album
                if "TALB" in tags:  # ID3v2 album
                    metadata["album"] = str(tags["TALB"][0])
                elif "ALBUM" in tags:  # Vorbis comment
                    metadata["album"] = str(tags["ALBUM"][0])

                # Genre
                if "TCON" in tags:  # ID3v2 genre
                    metadata["genre"] = str(tags["TCON"][0])
                elif "GENRE" in tags:  # Vorbis comment
                    metadata["genre"] = str(tags["GENRE"][0])

                # Year
                if "TDRC" in tags:  # ID3v2.4 recording time
                    year_str = str(tags["TDRC"][0])
                    try:
                        metadata["year"] = int(year_str[:4])  # Extract year part
                    except (ValueError, IndexError):
                        pass
                elif "TYER" in tags:  # ID3v2.3 year
                    try:
                        metadata["year"] = int(str(tags["TYER"][0]))
                    except ValueError:
                        pass
                elif "DATE" in tags:  # Vorbis comment
                    date_str = str(tags["DATE"][0])
                    try:
                        metadata["year"] = int(date_str[:4])
                    except (ValueError, IndexError):
                        pass

                # BPM
                if "TBPM" in tags:  # ID3v2 BPM
                    try:
                        metadata["bpm"] = float(str(tags["TBPM"][0]))
                    except ValueError:
                        pass
                elif "BPM" in tags:  # Vorbis comment
                    try:
                        metadata["bpm"] = float(str(tags["BPM"][0]))
                    except ValueError:
                        pass

                # Comment
                if "COMM::eng" in tags:  # ID3v2 comment
                    metadata["comment"] = str(tags["COMM::eng"][0])
                elif "COMMENT" in tags:  # Vorbis comment
                    metadata["comment"] = str(tags["COMMENT"][0])

            if metadata:  # Only log if we extracted meaningful metadata
                logger.debug(f"Extracted metadata from {file_path}: {metadata}")

        except Exception as e:
            logger.debug(
                f"Could not extract metadata from {file_path}: {e}"
            )  # Reduced to debug level        return metadata

    @staticmethod
    def extract_metadata_from_path(file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from file path structure.

        Rekordbox USB structure: Contents/Artist/Album/Track.mp3

        Args:
            file_path: Path to the audio file

        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {}

        try:
            parts = file_path.parts

            # Find "Contents" in the path to determine the structure
            contents_index = -1
            for i, part in enumerate(parts):
                if part.lower() == "contents":
                    contents_index = i
                    break

            if contents_index >= 0 and len(parts) > contents_index + 3:
                # Structure: .../Contents/Artist/Album/Track.ext
                artist = parts[contents_index + 1]
                album = parts[contents_index + 2]
                filename = parts[-1]

                # Clean up artist and album names
                metadata["artist"] = artist.replace("_", " ").strip()
                metadata["album"] = album.replace("_", " ").strip()

                # Extract title from filename (remove extension)
                title = Path(filename).stem
                # Remove common patterns like "Artist - Title"
                if " - " in title:
                    title_parts = title.split(" - ", 1)
                    if len(title_parts) == 2:
                        # Use the part after the dash as title
                        metadata["title"] = title_parts[1].strip()
                else:
                    metadata["title"] = title.strip()

                logger.debug(f"Extracted from path {file_path}: {metadata}")

        except Exception as e:
            logger.debug(f"Error extracting metadata from path {file_path}: {e}")

        return metadata

    @staticmethod
    def merge_metadata(
        pdb_metadata: Dict[str, Any],
        file_metadata: Dict[str, Any],
        path_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Merge metadata from different sources, with priority order:
        1. PDB metadata (highest priority)
        2. ID3 file metadata
        3. Path-based metadata (fallback)

        Args:
            pdb_metadata: Metadata from PDB parsing
            file_metadata: Metadata from ID3 tags
            path_metadata: Metadata from file path analysis

        Returns:
            Merged metadata dictionary
        """
        merged = {}

        # List of fields to merge
        fields = [
            "title",
            "artist",
            "album",
            "genre",
            "year",
            "bpm",
            "duration",
            "bitrate",
            "sample_rate",
            "comment",
        ]

        for field in fields:
            # Priority: PDB -> File -> Path
            if (
                pdb_metadata
                and isinstance(pdb_metadata, dict)
                and field in pdb_metadata
                and pdb_metadata[field] is not None
            ):
                merged[field] = pdb_metadata[field]
            elif (
                file_metadata
                and isinstance(file_metadata, dict)
                and field in file_metadata
                and file_metadata[field] is not None
            ):
                merged[field] = file_metadata[field]
            elif (
                path_metadata
                and isinstance(path_metadata, dict)
                and field in path_metadata
                and path_metadata[field] is not None
            ):
                merged[field] = path_metadata[field]

        return merged
