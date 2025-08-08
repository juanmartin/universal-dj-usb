"""Main converter class that orchestrates the conversion process."""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import time

from .models import Playlist, PlaylistTree, ConversionConfig, ConversionResult
from .rekordbox_parser import RekordboxParser, create_rekordbox_parser
from .nml_generator import TraktorNMLGenerator, create_nml_generator
from .m3u_generator import M3UGenerator, create_m3u_generator
from .utils import (
    detect_usb_drives,
    validate_rekordbox_export,
    create_directory,
    normalize_path,
    get_platform_specific_paths,
    setup_logging,
)

logger = logging.getLogger(__name__)


class RekordboxToTraktorConverter:
    """Main converter class for Rekordbox to Traktor playlist conversion."""

    def __init__(self, config: Optional[ConversionConfig] = None):
        """
        Initialize the converter.

        Args:
            config: Conversion configuration. If None, uses default config.
        """
        self.config = config or ConversionConfig()
        self.setup_logging()

        logger.info("Initialized Rekordbox to Traktor converter")
        logger.info(f"Configuration: {self.config}")

    def setup_logging(self) -> None:
        """Set up logging configuration."""
        paths = get_platform_specific_paths()
        log_file = paths["data"] / "logs" / "conversion.log"
        setup_logging("INFO", log_file)

    def detect_usb_drives(self) -> List[Path]:
        """
        Detect USB drives with Rekordbox exports.

        Returns:
            List of USB drive paths containing Rekordbox exports
        """
        logger.info("Detecting USB drives with Rekordbox exports...")
        drives = detect_usb_drives()
        logger.info(f"Found {len(drives)} USB drives with Rekordbox exports")
        return drives

    def convert_playlist(
        self, usb_drive_path: Path, playlist_name: str, output_path: Path
    ) -> ConversionResult:
        """
        Convert a single playlist from Rekordbox to Traktor NML format.

        Args:
            usb_drive_path: Path to the USB drive with Rekordbox export
            playlist_name: Name of the playlist to convert
            output_path: Path where the NML file should be saved

        Returns:
            ConversionResult with details of the conversion
        """
        start_time = time.time()

        try:
            logger.info(f"Converting playlist '{playlist_name}' from {usb_drive_path}")

            # Parse the Rekordbox database
            parser = create_rekordbox_parser(usb_drive_path)
            playlist = parser.get_playlist_by_name(playlist_name)

            if not playlist:
                return ConversionResult(
                    success=False,
                    playlist_name=playlist_name,
                    error_message=f"Playlist '{playlist_name}' not found",
                )

            # Generate NML file
            nml_generator = create_nml_generator(self.config)
            base_path = usb_drive_path if self.config.relative_paths else None

            success = nml_generator.generate_nml(playlist, output_path, base_path)

            if success:
                elapsed_time = time.time() - start_time
                logger.info(
                    f"Successfully converted '{playlist_name}' in {elapsed_time:.2f}s"
                )

                return ConversionResult(
                    success=True,
                    playlist_name=playlist_name,
                    output_file=output_path,
                    track_count=len(playlist.tracks),
                )
            else:
                return ConversionResult(
                    success=False,
                    playlist_name=playlist_name,
                    error_message="Failed to generate NML file",
                )

        except Exception as e:
            logger.error(f"Error converting playlist '{playlist_name}': {e}")
            return ConversionResult(
                success=False, playlist_name=playlist_name, error_message=str(e)
            )

    def convert_all_playlists(
        self,
        usb_drive_path: Path,
        output_dir: Path,
        playlist_filter: Optional[List[str]] = None,
    ) -> List[ConversionResult]:
        """
        Convert all playlists (or a filtered subset) from Rekordbox to Traktor NML format.

        Args:
            usb_drive_path: Path to the USB drive with Rekordbox export
            output_dir: Directory where NML files should be saved
            playlist_filter: Optional list of playlist names to convert. If None, converts all.

        Returns:
            List of ConversionResult objects for each playlist
        """
        start_time = time.time()
        results = []

        try:
            logger.info(f"Converting playlists from {usb_drive_path} to {output_dir}")

            # Ensure output directory exists
            create_directory(output_dir)

            # Parse all playlists
            parser = create_rekordbox_parser(usb_drive_path)
            playlist_tree = parser.parse_playlists()

            # Filter playlists if requested
            playlists_to_convert = []
            for playlist in playlist_tree.all_playlists.values():
                if not playlist.is_folder:  # Only convert actual playlists, not folders
                    if playlist_filter is None or playlist.name in playlist_filter:
                        playlists_to_convert.append(playlist)

            logger.info(f"Converting {len(playlists_to_convert)} playlists")

            # Determine if we should use relative paths based on output location
            # If output directory is on the USB drive, use relative paths for portability
            # If output directory is elsewhere, use absolute paths
            use_relative_paths = False
            base_path = None

            if self.config.relative_paths:
                try:
                    # Check if output directory is on the USB drive
                    output_dir.relative_to(usb_drive_path)
                    use_relative_paths = True
                    base_path = usb_drive_path
                    logger.info(
                        f"Output directory is on USB drive, using relative paths"
                    )
                except ValueError:
                    # Output directory is not on USB drive, use absolute paths
                    use_relative_paths = False
                    base_path = None
                    logger.info(
                        f"Output directory is not on USB drive, using absolute paths"
                    )
            else:
                # Configuration explicitly requests absolute paths
                use_relative_paths = False
                base_path = None
                logger.info(f"Configuration set to use absolute paths")

            # Handle different output formats
            formats_to_generate = []
            if self.config.output_format.lower() == "all":
                formats_to_generate = ["nml", "m3u", "m3u8"]
            else:
                formats_to_generate = [self.config.output_format.lower()]

            for playlist in playlists_to_convert:
                for output_format in formats_to_generate:
                    # Generate output filename with appropriate extension and format suffix
                    safe_name = self._sanitize_filename(playlist.name)

                    # Add format suffix if generating multiple formats ("all" mode)
                    if len(formats_to_generate) > 1:
                        # Use format suffix for multiple formats (e.g., "TEST-nml.nml")
                        if output_format == "nml":
                            output_path = output_dir / f"{safe_name}-nml.nml"
                        elif output_format == "m3u":
                            output_path = output_dir / f"{safe_name}-m3u.m3u"
                        elif output_format == "m3u8":
                            output_path = output_dir / f"{safe_name}-m3u8.m3u8"
                        else:
                            continue  # Skip unsupported formats
                    else:
                        # Single format mode - use standard naming
                        if output_format == "nml":
                            output_path = output_dir / f"{safe_name}.nml"
                        elif output_format == "m3u":
                            output_path = output_dir / f"{safe_name}.m3u"
                        elif output_format == "m3u8":
                            output_path = output_dir / f"{safe_name}.m3u8"
                        else:
                            continue  # Skip unsupported formats

                    # Convert playlist
                    result = self._convert_single_playlist_with_format(
                        playlist, output_path, base_path, output_format
                    )
                    results.append(result)

            # Log summary
            successful = sum(1 for r in results if r.success)
            total_time = time.time() - start_time

            logger.info(
                f"Conversion completed: {successful}/{len(results)} successful in {total_time:.2f}s"
            )

            return results

        except Exception as e:
            logger.error(f"Error during batch conversion: {e}")
            # Return error result for all requested playlists
            error_result = ConversionResult(
                success=False, playlist_name="<batch>", error_message=str(e)
            )
            return [error_result]

    def _convert_single_playlist_with_generator(
        self,
        playlist: Playlist,
        nml_generator: TraktorNMLGenerator,
        output_path: Path,
        base_path: Optional[Path],
    ) -> ConversionResult:
        """Convert a single playlist using the provided NML generator."""
        try:
            success = nml_generator.generate_nml(playlist, output_path, base_path)

            if success:
                return ConversionResult(
                    success=True,
                    playlist_name=playlist.name,
                    output_file=output_path,
                    track_count=len(playlist.tracks),
                )
            else:
                return ConversionResult(
                    success=False,
                    playlist_name=playlist.name,
                    error_message="Failed to generate NML file",
                )

        except Exception as e:
            return ConversionResult(
                success=False, playlist_name=playlist.name, error_message=str(e)
            )

    def _convert_single_playlist_with_format(
        self,
        playlist: Playlist,
        output_path: Path,
        base_path: Optional[Path],
        output_format: str,
    ) -> ConversionResult:
        """Convert a single playlist using the specified output format."""
        try:
            if output_format.lower() == "nml":
                nml_generator = create_nml_generator(self.config)
                success = nml_generator.generate_nml(playlist, output_path, base_path)
            elif output_format.lower() == "m3u":
                m3u_generator = create_m3u_generator(self.config)
                success = m3u_generator.generate_m3u(
                    playlist, output_path, base_path, extended=False
                )
            elif output_format.lower() == "m3u8":
                m3u_generator = create_m3u_generator(self.config)
                success = m3u_generator.generate_m3u(
                    playlist, output_path, base_path, extended=True
                )
            else:
                return ConversionResult(
                    success=False,
                    playlist_name=playlist.name,
                    error_message=f"Unsupported output format: {output_format}",
                )

            if success:
                return ConversionResult(
                    success=True,
                    playlist_name=playlist.name,
                    output_file=output_path,
                    track_count=len(playlist.tracks),
                )
            else:
                return ConversionResult(
                    success=False,
                    playlist_name=playlist.name,
                    error_message=f"Failed to generate {output_format.upper()} file",
                )

        except Exception as e:
            return ConversionResult(
                success=False, playlist_name=playlist.name, error_message=str(e)
            )

    def list_playlists(self, usb_drive_path: Path) -> List[str]:
        """
        List all available playlists on a USB drive.

        Args:
            usb_drive_path: Path to the USB drive with Rekordbox export

        Returns:
            List of playlist names
        """
        try:
            parser = create_rekordbox_parser(usb_drive_path)
            playlists = parser.get_all_playlists()

            # Filter out folders, return only actual playlists
            playlist_names = [
                playlist.name for playlist in playlists if not playlist.is_folder
            ]

            logger.info(f"Found {len(playlist_names)} playlists")
            return playlist_names

        except Exception as e:
            logger.error(f"Error listing playlists: {e}")
            return []

    def get_playlist_info(
        self, usb_drive_path: Path, playlist_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific playlist.

        Args:
            usb_drive_path: Path to the USB drive with Rekordbox export
            playlist_name: Name of the playlist

        Returns:
            Dictionary with playlist information or None if not found
        """
        try:
            parser = create_rekordbox_parser(usb_drive_path)
            playlist = parser.get_playlist_by_name(playlist_name)

            if not playlist:
                return None

            return {
                "name": playlist.name,
                "track_count": playlist.track_count,
                "total_duration": playlist.total_duration,
                "is_folder": playlist.is_folder,
                "tracks": [
                    {
                        "title": track.title,
                        "artist": track.artist,
                        "album": track.album,
                        "duration": track.duration,
                        "file_path": str(track.file_path),
                    }
                    for track in playlist.tracks
                ],
            }

        except Exception as e:
            logger.error(f"Error getting playlist info: {e}")
            return None

    def validate_usb_drive(self, usb_drive_path: Path) -> bool:
        """
        Validate that a USB drive contains a valid Rekordbox export.

        Args:
            usb_drive_path: Path to the USB drive

        Returns:
            True if valid, False otherwise
        """
        export_path = usb_drive_path / "PIONEER" / "rekordbox" / "export.pdb"
        return validate_rekordbox_export(export_path)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename for safe filesystem usage."""
        import re

        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        filename = filename.strip(". ")
        return filename[:200]  # Limit length

    def get_conversion_progress(self, total_playlists: int, completed: int) -> float:
        """
        Calculate conversion progress as a percentage.

        Args:
            total_playlists: Total number of playlists to convert
            completed: Number of playlists completed

        Returns:
            Progress as a percentage (0.0 to 100.0)
        """
        if total_playlists == 0:
            return 100.0
        return (completed / total_playlists) * 100.0

    def estimate_time_remaining(
        self, total_playlists: int, completed: int, elapsed_time: float
    ) -> float:
        """
        Estimate remaining conversion time.

        Args:
            total_playlists: Total number of playlists to convert
            completed: Number of playlists completed
            elapsed_time: Time elapsed so far in seconds

        Returns:
            Estimated remaining time in seconds
        """
        if completed == 0:
            return 0.0

        avg_time_per_playlist = elapsed_time / completed
        remaining_playlists = total_playlists - completed

        return remaining_playlists * avg_time_per_playlist
