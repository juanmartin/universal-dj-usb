"""M3U8 playlist generator with extended metadata."""

from pathlib import Path
from urllib.parse import quote

from .base import BaseGenerator
from ..models import Playlist, ConversionResult


class M3U8Generator(BaseGenerator):
    """Generator for M3U8 playlist format with extended metadata."""

    @property
    def file_extension(self) -> str:
        """Return the file extension for M3U8 format."""
        if hasattr(self.config, "use_format_suffix") and self.config.use_format_suffix:
            return "-M3U8.m3u8"
        else:
            return ".m3u8"

    def generate(
        self, playlist: Playlist, output_path: Path, usb_path: Path = None
    ) -> ConversionResult:
        """Generate an M3U8 playlist file with extended metadata."""
        try:
            filename = f"{self._sanitize_filename(playlist.name)}{self.file_extension}"
            output_file = output_path / filename

            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)

            lines = ["#EXTM3U"]
            warnings = []

            for track in playlist.tracks:
                # Extended metadata
                extinf_parts = []

                # Duration
                duration = int(track.duration) if track.duration else -1

                # Build track info with additional metadata
                track_info = f"{track.artist} - {track.title}"

                # Add extended info
                extended_info = []
                if track.album:
                    extended_info.append(f"Album: {track.album}")
                if track.year:
                    extended_info.append(f"Year: {track.year}")
                if track.genre:
                    extended_info.append(f"Genre: {track.genre}")
                if track.bpm:
                    extended_info.append(f"BPM: {track.bpm:.1f}")

                if extended_info:
                    track_info += f" ({', '.join(extended_info)})"

                lines.append(f"#EXTINF:{duration},{track_info}")

                # Add file path (URL encode for M3U8 compatibility)
                if self.config.relative_paths:
                    track_path = self._normalize_path(track.file_path, output_path)
                else:
                    track_path = self._normalize_path(track.file_path)

                # URL encode the path for M3U8 compatibility
                track_path = quote(track_path, safe="/:")

                # Check if file exists (warning only)
                if not track.file_path.exists():
                    warnings.append(f"File not found: {track.file_path}")

                lines.append(track_path)

            # Write the M3U8 file
            content = "\\n".join(lines)
            with open(
                output_file, "w", encoding="utf-8"
            ) as f:  # M3U8 should always be UTF-8
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
                error_message=f"Failed to generate M3U8: {str(e)}",
            )
