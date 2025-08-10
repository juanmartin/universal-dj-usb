"""M3U playlist generator."""

from pathlib import Path
from typing import List

from .base import BaseGenerator
from ..models import Playlist, ConversionResult


class M3UGenerator(BaseGenerator):
    """Generator for M3U playlist format."""

    @property
    def file_extension(self) -> str:
        """Return the file extension for M3U format."""
        if hasattr(self.config, "use_format_suffix") and self.config.use_format_suffix:
            return "-M3U.m3u"
        else:
            return ".m3u"

    def generate(
        self, playlist: Playlist, output_path: Path, usb_path: Path = None
    ) -> ConversionResult:
        """Generate an M3U playlist file."""
        try:
            filename = f"{self._sanitize_filename(playlist.name)}{self.file_extension}"
            output_file = output_path / filename

            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)

            lines = ["#EXTM3U"]
            warnings = []

            for track in playlist.tracks:
                # Add track info line (optional in M3U but commonly used)
                duration = int(track.duration) if track.duration else -1
                track_info = f"{track.artist} - {track.title}"
                lines.append(f"#EXTINF:{duration},{track_info}")

                # Add file path
                if self.config.relative_paths:
                    # Use relative path from output location
                    track_path = self._normalize_path(track.file_path, output_path)
                else:
                    track_path = self._normalize_path(track.file_path)

                # Check if file exists (warning only)
                if not track.file_path.exists():
                    warnings.append(f"File not found: {track.file_path}")

                lines.append(track_path)

            # Write the M3U file
            content = "\\n".join(lines)
            with open(output_file, "w", encoding=self.config.encoding) as f:
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
