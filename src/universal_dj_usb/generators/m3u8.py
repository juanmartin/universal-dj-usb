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
        return ".m3u8"

    def generate(
        self, playlist: Playlist, output_path: Path, usb_path: Path = None
    ) -> ConversionResult:
        """Generate an M3U8 playlist file with extended metadata."""
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

                    # Build track info with additional metadata for M3U8
                    track_info = f"{track.artist} - {track.title}"

                    # Add extended metadata for M3U8
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

                # Determine path type based on M3U-specific option
                if self.config.m3u_absolute_paths:
                    # Use absolute paths - construct full system path
                    if usb_path and not track.file_path.is_absolute():
                        # Remove leading slash from track path and join with USB path
                        track_path_str = str(track.file_path)
                        if track_path_str.startswith("/"):
                            track_path_str = track_path_str[1:]
                        full_path = usb_path / track_path_str
                        track_path = str(full_path)
                    else:
                        track_path = str(track.file_path)
                else:
                    # Use relative paths - keep the original working logic
                    track_path = self._normalize_path(track.file_path, output_path)

                # URL encode the path for M3U8 compatibility if needed
                if self.config.m3u_extended:
                    track_path = quote(track_path, safe="/:")

                lines.append(track_path)

            # Write the M3U8 file with UTF-8 encoding
            content = "\n".join(lines)
            with open(output_file, "w", encoding="utf-8") as f:
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
