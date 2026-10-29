"""Shared playlist export orchestration for the CLI and GUI."""

import logging
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable, List, Optional, TYPE_CHECKING

from .copier import PlaylistCopyResult, copy_playlist_files
from .generators import M3U8Generator, M3UGenerator, NMLGenerator
from .generators.base import BaseGenerator
from .models import ConversionConfig, ConversionResult, Playlist
from .paths import sanitize_filename, unique_name

if TYPE_CHECKING:
    from .parser import RekordboxParser

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, int], None]


@dataclass
class ExportResult:
    """Combined result of copying files and generating playlist files."""

    conversions: List[ConversionResult] = field(default_factory=list)
    copies: List[PlaylistCopyResult] = field(default_factory=list)

    @property
    def successful_conversions(self) -> List[ConversionResult]:
        return [result for result in self.conversions if result.success]

    @property
    def failed_conversions(self) -> List[ConversionResult]:
        return [result for result in self.conversions if not result.success]

    @property
    def total_copied(self) -> int:
        return sum(result.copied_count for result in self.copies)

    @property
    def total_skipped(self) -> int:
        return sum(result.skipped_count for result in self.copies)

    @property
    def total_duplicates(self) -> int:
        return sum(result.duplicate_count for result in self.copies)

    @property
    def total_missing(self) -> int:
        return sum(result.missing_count for result in self.copies)

    @property
    def total_errors(self) -> int:
        return sum(result.error_count for result in self.copies)

    @property
    def success(self) -> bool:
        conversions_ok = all(result.success for result in self.conversions)
        copies_ok = all(result.success for result in self.copies)
        return conversions_ok and copies_ok


def create_generators(config: ConversionConfig) -> List[BaseGenerator]:
    """Build the generator list for a conversion config."""
    output_format = config.output_format.lower()
    if output_format == "all":
        return [NMLGenerator(config), M3UGenerator(config), M3U8Generator(config)]
    if output_format == "nml":
        return [NMLGenerator(config)]
    if output_format == "m3u":
        return [M3UGenerator(config)]
    if output_format == "m3u8":
        return [M3U8Generator(config)]
    return []


def build_output_filename(
    playlist_name: str, generator: BaseGenerator, config: ConversionConfig
) -> str:
    """Build the playlist filename, including the optional format suffix."""
    filename = sanitize_filename(playlist_name)
    if config.use_format_suffix:
        filename = f"{filename}_{generator.file_extension.lstrip('.')}"
    return f"{filename}{generator.file_extension}"


def export_playlists(
    playlists: List[Playlist],
    usb_path: Path,
    output_dir: Path,
    config: ConversionConfig,
    parser: Optional["RekordboxParser"] = None,
    enhance: bool = False,
    generate_playlists: bool = True,
    progress_callback: Optional[ProgressCallback] = None,
) -> ExportResult:
    """Copy playlist audio and/or generate playlist files.

    This is the single orchestration path used by the CLI and GUI. When
    ``config.copy_files`` is true, audio is copied into
    ``<output_dir>/<playlist name>/`` and generated playlists reference those
    copies.
    """
    result = ExportResult()
    output_dir.mkdir(parents=True, exist_ok=True)

    working_playlists = playlists
    if enhance and parser is not None:
        _emit(progress_callback, "Enhancing track metadata...", 0)
        working_playlists = [
            parser.enhance_playlist_tracks(playlist, usb_path)
            for playlist in playlists
        ]

    generators = create_generators(config) if generate_playlists else []
    total_playlists = max(len(working_playlists), 1)
    used_folder_names: set[str] = set()

    for playlist_index, playlist in enumerate(working_playlists):
        playlist_percent = int((playlist_index / total_playlists) * 100)
        folder_name = unique_name(
            sanitize_filename(playlist.name), used_folder_names
        )
        used_folder_names.add(folder_name.casefold())

        copy_result: Optional[PlaylistCopyResult] = None
        tracks_for_output = playlist.tracks
        generator_usb_path = usb_path

        if config.copy_files:
            _emit(
                progress_callback,
                f"Copying '{playlist.name}'...",
                playlist_percent,
            )

            def on_file(
                file_result, current: int, total: int, name: str = playlist.name
            ) -> None:
                _emit(
                    progress_callback,
                    f"Copying '{name}': {file_result.source.name} ({current}/{total})",
                    playlist_percent,
                )

            copy_result = copy_playlist_files(
                playlist=playlist,
                usb_path=usb_path,
                output_dir=output_dir,
                folder_name=folder_name,
                number_files=config.number_files,
                overwrite=config.overwrite_files,
                progress_callback=on_file,
            )
            result.copies.append(copy_result)

            tracks_for_output = [
                replace(track, file_path=copy_result.destinations_by_index[index])
                for index, track in enumerate(playlist.tracks)
                if index in copy_result.destinations_by_index
            ]
            generator_usb_path = output_dir

        if not generate_playlists:
            continue

        output_playlist = Playlist(
            id=playlist.id,
            name=playlist.name,
            tracks=tracks_for_output,
            is_folder=playlist.is_folder,
            parent_id=playlist.parent_id,
        )

        if config.copy_files and not tracks_for_output:
            message = f"No tracks could be copied for playlist '{playlist.name}'"
            for generator in generators:
                result.conversions.append(
                    ConversionResult(
                        success=False,
                        playlist_name=playlist.name,
                        error_message=message,
                    )
                )
            continue

        for generator in generators:
            output_path = output_dir / build_output_filename(
                playlist.name, generator, config
            )
            conversion = generator.generate(
                output_playlist, output_path, generator_usb_path
            )
            if copy_result is not None:
                _add_copy_warnings(conversion, copy_result)
            result.conversions.append(conversion)

        _emit(
            progress_callback,
            f"Exported '{playlist.name}'",
            int(((playlist_index + 1) / total_playlists) * 100),
        )

    _emit(progress_callback, "Export complete!", 100)
    return result


def _add_copy_warnings(
    conversion: ConversionResult, copy_result: PlaylistCopyResult
) -> None:
    """Add copy problems to a generated playlist's warnings."""
    unavailable = copy_result.missing_count + copy_result.error_count
    if unavailable:
        conversion.warnings.append(
            f"{unavailable} track(s) could not be copied and were excluded"
        )
    for item in copy_result.files:
        if item.status.value in ("missing", "error") and item.error:
            conversion.warnings.append(item.error)


def _emit(
    callback: Optional[ProgressCallback], message: str, percentage: int
) -> None:
    if callback:
        callback(message, max(0, min(100, percentage)))
