"""M3U and M3U8 playlist generator for playlist conversion."""

import logging
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

from .models import Playlist, Track, ConversionConfig
from .utils import sanitize_filename

logger = logging.getLogger(__name__)


class M3UGenerator:
    """Generates M3U and M3U8 playlist files from playlist data."""

    def __init__(self, config: ConversionConfig):
        """
        Initialize the M3U generator.

        Args:
            config: Conversion configuration
        """
        self.config = config

    def generate_m3u(
        self,
        playlist: Playlist,
        output_path: Path,
        base_path: Optional[Path] = None,
        extended: bool = False,
    ) -> bool:
        """
        Generate an M3U file for a single playlist.

        Args:
            playlist: Playlist to convert
            output_path: Path to save the M3U file
            base_path: Base path for relative file paths (usually the USB drive root)
            extended: Whether to generate extended M3U format with metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(
                f"Generating M3U{'8' if extended else ''} for playlist: {playlist.name}"
            )

            # Prepare playlist content
            lines = []

            # Add M3U header if extended format
            if extended:
                lines.append("#EXTM3U")
                lines.append("")

            # Add tracks
            for track in playlist.tracks:
                if extended:
                    # Add extended info line
                    duration = int(track.duration) if track.duration else -1
                    artist = track.artist or "Unknown Artist"
                    title = track.title or track.filename
                    lines.append(f"#EXTINF:{duration},{artist} - {title}")

                # Add file path - use output_path.parent as the reference for relative paths
                file_path = self._get_track_path(track, base_path, output_path.parent)
                lines.append(file_path)

                if extended:
                    lines.append("")  # Empty line between tracks for readability

            # Write to file
            return self._write_m3u_file(lines, output_path)

        except Exception as e:
            logger.error(f"Failed to generate M3U for {playlist.name}: {e}")
            return False

    def generate_multiple_m3u(
        self,
        playlists: List[Playlist],
        output_dir: Path,
        base_path: Optional[Path] = None,
        extended: bool = False,
        format_suffix: Optional[str] = None,
    ) -> List[Path]:
        """
        Generate M3U files for multiple playlists.

        Args:
            playlists: List of playlists to convert
            output_dir: Directory to save M3U files
            base_path: Base path for relative file paths
            extended: Whether to generate extended M3U format
            format_suffix: Optional suffix to add to filename (e.g., "m3u" for "all" format mode)

        Returns:
            List of successfully created M3U file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        created_files = []

        for i, playlist in enumerate(playlists):
            if self.config.file_naming == "sequential":
                base_name = f"{i+1:03d}_{sanitize_filename(playlist.name)}"
            else:
                base_name = sanitize_filename(playlist.name)

            # Add format suffix if specified (for "all" format mode)
            if format_suffix:
                filename = f"{base_name}-{format_suffix}.m3u{'8' if extended else ''}"
            else:
                filename = f"{base_name}.m3u{'8' if extended else ''}"

            output_path = output_dir / filename

            if self.generate_m3u(playlist, output_path, base_path, extended):
                created_files.append(output_path)

        return created_files

    def _get_track_path(
        self,
        track: Track,
        base_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ) -> str:
        """
        Get the appropriate track path for the M3U file.

        Args:
            track: Track to get path for
            base_path: Base path for relative paths (usually the USB drive root)
            output_dir: Directory where the M3U file will be saved (for relative path calculation)

        Returns:
            Track path string
        """
        track_path = track.file_path

        # Ensure we have an absolute path to work with
        if not track_path.is_absolute():
            if base_path:
                track_path = base_path / track_path
            else:
                track_path = track_path.resolve()

        if self.config.relative_paths and base_path and output_dir:
            try:
                # Make the path relative to the output directory
                # This ensures the playlist works correctly regardless of where it's saved
                rel_path = track_path.relative_to(output_dir)
                return str(rel_path)
            except ValueError:
                # If the track is not under the output directory, try making it relative to a common ancestor
                try:
                    # Calculate relative path from output_dir to the track
                    # Find how many levels up we need to go from output_dir to reach the track
                    output_parts = output_dir.parts
                    track_parts = track_path.parts

                    logger.debug(f"Output parts: {output_parts}")
                    logger.debug(f"Track parts: {track_parts}")

                    # Find common prefix
                    common_parts = []
                    for i in range(min(len(output_parts), len(track_parts))):
                        if output_parts[i] == track_parts[i]:
                            common_parts.append(output_parts[i])
                        else:
                            break

                    logger.debug(f"Common parts: {common_parts}")

                    # Calculate how many levels up from output_dir to common ancestor
                    up_levels = len(output_parts) - len(common_parts)
                    # Get the remaining path from common ancestor to track
                    remaining_track_parts = track_parts[len(common_parts) :]

                    logger.debug(f"Up levels: {up_levels}")
                    logger.debug(f"Remaining track parts: {remaining_track_parts}")

                    # Build the relative path using .. to go up from output_dir
                    rel_path = Path(*([".."] * up_levels)) / Path(
                        *remaining_track_parts
                    )

                    logger.debug(f"Final relative path: {rel_path}")

                    return str(rel_path)
                except (ValueError, OSError):
                    # If all relative path attempts fail, use absolute path
                    logger.warning(
                        f"Cannot create relative path for {track_path} relative to {output_dir}, using absolute path"
                    )
                    return str(track_path)
        else:
            # Use absolute path - this works regardless of where the playlist is saved
            return str(track_path)

    def _write_m3u_file(self, lines: List[str], output_path: Path) -> bool:
        """Write the M3U lines to a file."""
        try:
            with open(output_path, "w", encoding=self.config.encoding) as f:
                f.write("\n".join(lines))
                if lines:  # Add final newline if there's content
                    f.write("\n")

            logger.info(f"Successfully wrote M3U file: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to write M3U file {output_path}: {e}")
            return False


def create_m3u_generator(config: ConversionConfig) -> M3UGenerator:
    """
    Factory function to create an M3UGenerator.

    Args:
        config: Conversion configuration

    Returns:
        Configured M3UGenerator instance
    """
    return M3UGenerator(config)
