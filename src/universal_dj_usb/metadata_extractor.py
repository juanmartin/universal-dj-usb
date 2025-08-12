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

                # Musical Key - crucial for DJs
                if "TKEY" in tags:  # ID3v2 key
                    metadata["key"] = str(tags["TKEY"][0])
                elif "INITIALKEY" in tags:  # Vorbis comment / Traktor key
                    metadata["key"] = str(tags["INITIALKEY"][0])

                # Rating (for DJ software compatibility)
                if "POPM:Windows Media Player 9 Series" in tags:  # WMP rating
                    try:
                        rating_data = tags["POPM:Windows Media Player 9 Series"]
                        if hasattr(rating_data, "rating"):
                            # Convert 0-255 scale to 0-5 stars
                            metadata["rating"] = int(rating_data.rating / 51)
                    except:
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
            )  # Reduced to debug level

        return metadata

    @staticmethod
    def extract_metadata_from_path(file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from file path structure.

        Rekordbox USB structure: <USB-mount>/Contents/<Artist>/<Album>/<tracks...>
        This is the most reliable source for artist and album information.

        Args:
            file_path: Path to the audio file

        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {}

        try:
            parts = file_path.parts

            # Find "Contents" in the path to determine the Rekordbox structure
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

                # Use folder names as-is, only replacing underscores with spaces
                metadata["artist"] = artist.replace("_", " ").strip()
                metadata["album"] = album.replace("_", " ").strip()

                # Extract title from filename (remove extension and track numbers)
                title = Path(filename).stem
                # Only remove numerical prefixes like "01 - " or "01. " from title
                title_clean = re.sub(r"^\d+\s*[-.]?\s*", "", title)
                if title_clean:
                    metadata["title"] = title_clean.strip()
                else:
                    metadata["title"] = title.strip()

                    # Fallback: try to extract artist from any path that has enough parts
            elif len(parts) >= 3 and not metadata.get("artist"):
                # Try different patterns for artist extraction
                # Pattern 1: /some/path/Artist/Album/Track.mp3 (artist in second-to-last directory)
                if len(parts) >= 3:
                    potential_artist = parts[-3]  # Third from end
                    # Be more selective about what looks like an artist directory
                    if (
                        potential_artist.lower()
                        not in [
                            "music",
                            "audio",
                            "songs",
                            "tracks",
                            "files",
                            "path",
                            "random",
                            "tmp",
                            "temp",
                            "downloads",
                            "desktop",
                            "documents",
                            "users",
                            "home",
                            "volumes",
                        ]
                        and len(potential_artist) > 2
                        and not potential_artist.isdigit()
                    ):
                        metadata["artist"] = potential_artist.replace("_", " ").strip()

                # Pattern 2: /some/path/Artist/Track.mp3 (artist in parent directory)
                if not metadata.get("artist") and len(parts) >= 2:
                    potential_artist = parts[-2]  # Second from end (parent directory)
                    # Be more selective about what looks like an artist directory
                    if (
                        potential_artist.lower()
                        not in [
                            "music",
                            "audio",
                            "songs",
                            "tracks",
                            "files",
                            "path",
                            "random",
                            "tmp",
                            "temp",
                            "downloads",
                            "desktop",
                            "documents",
                            "users",
                            "home",
                            "volumes",
                            "dirs",
                            "nested",
                        ]
                        and len(potential_artist) > 2
                        and not potential_artist.isdigit()
                    ):
                        metadata["artist"] = potential_artist.replace("_", " ").strip()

            # Final fallback: extract from filename if still no artist found
            if not metadata.get("artist"):
                filename = Path(file_path).stem

                # Pattern: "Artist - Title"
                if " - " in filename:
                    filename_parts = filename.split(" - ", 1)
                    if len(filename_parts) == 2:
                        potential_artist = filename_parts[0].strip()
                        # Basic validation - artist name should be reasonable length
                        if len(potential_artist) > 1 and len(potential_artist) < 100:
                            metadata["artist"] = potential_artist
                            if not metadata.get("title"):
                                metadata["title"] = filename_parts[1].strip()

            # Minimal cleaning only for folder-based extraction - just underscores to spaces
            if metadata.get("artist"):
                metadata["artist"] = metadata["artist"].replace("_", " ").strip()
            if metadata.get("album"):
                metadata["album"] = metadata["album"].replace("_", " ").strip()

            # Clean up extracted metadata
            if metadata.get("artist"):
                # Remove numerical prefixes and common patterns
                artist_clean = re.sub(r"^\d+\s*[-.]?\s*", "", metadata["artist"])
                if artist_clean:
                    metadata["artist"] = artist_clean

                # Remove brackets and parentheses content
                metadata["artist"] = re.sub(
                    r"\[.*?\]|\(.*?\)", "", metadata["artist"]
                ).strip()

            if metadata.get("album"):
                # Remove numerical prefixes and common patterns
                album_clean = re.sub(r"^\d+\s*[-.]?\s*", "", metadata["album"])
                if album_clean:
                    metadata["album"] = album_clean

                # Remove brackets and parentheses content
                metadata["album"] = re.sub(
                    r"\[.*?\]|\(.*?\)", "", metadata["album"]
                ).strip()

            if metadata:
                logger.debug(
                    f"Final extracted metadata from path {file_path}: {metadata}"
                )

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

        # List of fields to merge - expanded for rich DJ metadata
        fields = [
            "title",
            "artist",
            "album",
            "genre",
            "year",
            "bpm",
            "key",  # Musical key - crucial for DJs
            "duration",
            "bitrate",
            "sample_rate",
            "comment",
            "rating",  # Star rating
            "date_added",  # When added to collection
        ]

        # Helper function to check if a value is valid (not None, not empty, not "Unknown" variants)
        def is_valid_value(value):
            if value is None:
                return False
            if isinstance(value, str):
                cleaned = value.strip().lower()
                if (
                    not cleaned
                    or cleaned == "unknown"
                    or cleaned == "unknownalbum"
                    or cleaned == "unknownartist"
                    or cleaned.startswith("unknown[id:")
                    or cleaned.startswith("unknownalbum")
                    or cleaned.startswith("unknownartist")
                ):
                    return False
            return True

        for field in fields:
            # Special handling for artist and album - prioritize path over file for Rekordbox reliability
            if field in ["artist", "album"]:
                # Priority for artist/album: PDB (if valid) -> Path -> File
                if (
                    pdb_metadata
                    and field in pdb_metadata
                    and is_valid_value(pdb_metadata[field])
                ):
                    merged[field] = pdb_metadata[field]
                elif (
                    path_metadata
                    and field in path_metadata
                    and is_valid_value(path_metadata[field])
                ):
                    merged[field] = path_metadata[field]
                elif (
                    file_metadata
                    and field in file_metadata
                    and is_valid_value(file_metadata[field])
                ):
                    merged[field] = file_metadata[field]

            # Special handling for BPM and key - these are critical for DJs, prioritize PDB then file
            elif field in ["bpm", "key"]:
                # Priority for BPM/key: PDB -> File -> Path (PDB and ID3 are more accurate for these)
                if (
                    pdb_metadata
                    and field in pdb_metadata
                    and is_valid_value(pdb_metadata[field])
                ):
                    merged[field] = pdb_metadata[field]
                elif (
                    file_metadata
                    and field in file_metadata
                    and is_valid_value(file_metadata[field])
                ):
                    merged[field] = file_metadata[field]
                elif (
                    path_metadata
                    and field in path_metadata
                    and is_valid_value(path_metadata[field])
                ):
                    merged[field] = path_metadata[field]

            # Standard priority for other fields: PDB -> File -> Path
            else:
                if (
                    pdb_metadata
                    and field in pdb_metadata
                    and is_valid_value(pdb_metadata[field])
                ):
                    merged[field] = pdb_metadata[field]
                elif (
                    file_metadata
                    and field in file_metadata
                    and is_valid_value(file_metadata[field])
                ):
                    merged[field] = file_metadata[field]
                elif (
                    path_metadata
                    and field in path_metadata
                    and is_valid_value(path_metadata[field])
                ):
                    merged[field] = path_metadata[field]

        # Apply final fallback logic for artist extraction
        # If we still don't have an artist, try to extract from title using common patterns
        if (
            "artist" not in merged or not is_valid_value(merged.get("artist"))
        ) and "title" in merged:
            artist_from_title = AudioMetadataExtractor._extract_artist_from_title(
                merged["title"]
            )
            if artist_from_title and is_valid_value(artist_from_title):
                merged["artist"] = artist_from_title
                logger.debug(f"Extracted artist from title: {artist_from_title}")

        return merged

    @staticmethod
    def _extract_artist_from_title(title: str) -> Optional[str]:
        """
        Extract artist name from track title using common patterns.

        Common DJ track title patterns:
        - "Artist - Track Name"
        - "Artist - Track Name (Remix)"
        - "Artist ft. Other - Track Name"

        Args:
            title: Track title string

        Returns:
            Extracted artist name or None if no pattern matches
        """
        if not title or not isinstance(title, str):
            return None

        title = title.strip()

        # Pattern: "Artist - Track Name" (most common)
        if " - " in title:
            potential_artist = title.split(" - ")[0].strip()

            # Basic validation - artist shouldn't be too long or contain certain patterns
            if (
                len(potential_artist) > 0
                and len(potential_artist) <= 50  # Reasonable artist name length
                and not potential_artist.lower().startswith("track")
                and not potential_artist.lower().startswith("unknown")
                and not potential_artist.isdigit()  # Not just numbers
            ):
                return potential_artist

        return None
