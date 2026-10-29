"""M3U playlist generator."""

import logging
from pathlib import Path
from typing import List

from .base import BaseGenerator
from ..models import Playlist, ConversionResult
from ..paths import resolve_track_source

logger = logging.getLogger(__name__)


class M3UGenerator(BaseGenerator):
    """Generator for M3U playlist format."""

    @property
    def file_extension(self) -> str:
        """Return the file extension for M3U format."""
        return ".m3u"

    def generate(
        self, playlist: Playlist, output_path: Path, usb_path: Path = None
    ) -> ConversionResult:
        """Generate an M3U playlist file."""
        try:
            # Use the output_path directly as provided by the caller
            output_file = output_path

            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)

            lines = []
            warnings = []

            # Add header if using extended format
            if self.config.m3u_extended:
                lines.append("#EXTM3U")

            for track in playlist.tracks:
                # Add extended info if using extended format
                if self.config.m3u_extended:
                    duration = int(track.duration) if track.duration else -1
                    track_info = f"{track.artist} - {track.title}"
                    lines.append(f"#EXTINF:{duration},{track_info}")

                # Determine path type based on M3U-specific option
                if self.config.m3u_absolute_paths:
                    track_path = str(resolve_track_source(track.file_path, usb_path))
                else:
                    track_path = self._normalize_path(
                        resolve_track_source(track.file_path, usb_path),
                        output_path.parent,
                    )

                lines.append(track_path)

            # Write the M3U file with appropriate encoding
            content = "\n".join(lines)
            encoding = "ascii" if self.file_extension.endswith(".m3u") else "utf-8"

            with open(output_file, "w", encoding=encoding) as f:
                f.write(content)

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
                error_message=f"Failed to generate M3U: {str(e)}",
            )
