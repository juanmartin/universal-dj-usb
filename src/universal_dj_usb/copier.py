"""Copy the audio files referenced by a playlist into a per-playlist folder."""

import logging
import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .models import Playlist
from .paths import resolve_track_source, sanitize_filename, unique_name

logger = logging.getLogger(__name__)


class CopyStatus(Enum):
    """Outcome of copying one track."""

    COPIED = "copied"
    SKIPPED = "skipped"
    DUPLICATE = "duplicate"
    MISSING = "missing"
    ERROR = "error"


@dataclass
class FileCopyResult:
    """Outcome for one track in a playlist copy operation."""

    track_title: str
    source: Path
    destination: Optional[Path]
    status: CopyStatus
    error: Optional[str] = None


@dataclass
class PlaylistCopyResult:
    """Outcome for copying all tracks in one playlist."""

    playlist_name: str
    destination_folder: Path
    files: List[FileCopyResult] = field(default_factory=list)
    destinations_by_index: Dict[int, Path] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def copied_count(self) -> int:
        return sum(1 for item in self.files if item.status == CopyStatus.COPIED)

    @property
    def skipped_count(self) -> int:
        return sum(1 for item in self.files if item.status == CopyStatus.SKIPPED)

    @property
    def duplicate_count(self) -> int:
        return sum(1 for item in self.files if item.status == CopyStatus.DUPLICATE)

    @property
    def missing_count(self) -> int:
        return sum(1 for item in self.files if item.status == CopyStatus.MISSING)

    @property
    def error_count(self) -> int:
        return sum(1 for item in self.files if item.status == CopyStatus.ERROR)

    @property
    def available_count(self) -> int:
        """Tracks that have a usable file in the destination folder."""
        return self.copied_count + self.skipped_count + self.duplicate_count

    @property
    def success(self) -> bool:
        return self.error is None


def copy_playlist_files(
    playlist: Playlist,
    usb_path: Path,
    output_dir: Path,
    folder_name: Optional[str] = None,
    number_files: bool = False,
    overwrite: bool = False,
    progress_callback: Optional[Callable[[FileCopyResult, int, int], None]] = None,
) -> PlaylistCopyResult:
    """Copy every audio file in *playlist* into ``output_dir/<folder_name>``.

    Files keep their original basename. Existing files are skipped unless
    *overwrite* is true. Missing sources and copy errors are recorded in the
    result instead of aborting the operation.
    """
    usb_path = usb_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    folder = output_dir / (folder_name or sanitize_filename(playlist.name))
    result = PlaylistCopyResult(
        playlist_name=playlist.name,
        destination_folder=folder,
    )

    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        result.error = f"Could not create destination folder {folder}: {exc}"
        logger.error(result.error)
        return result

    total = len(playlist.tracks)
    number_width = max(2, len(str(total)))
    used_names: set[str] = set()
    source_to_destination: Dict[Path, Path] = {}

    for index, track in enumerate(playlist.tracks):
        source = resolve_track_source(track.file_path, usb_path)
        file_result: FileCopyResult

        if not source.exists() or not source.is_file():
            file_result = FileCopyResult(
                track_title=track.title,
                source=source,
                destination=None,
                status=CopyStatus.MISSING,
                error=f"Source file not found: {source}",
            )
            result.files.append(file_result)
            _notify(progress_callback, file_result, index, total)
            continue

        resolved_source = source.resolve()

        # Without numbering, the same physical file only needs one copy.
        if not number_files and resolved_source in source_to_destination:
            destination = source_to_destination[resolved_source]
            file_result = FileCopyResult(
                track_title=track.title,
                source=source,
                destination=destination,
                status=CopyStatus.DUPLICATE,
            )
            result.files.append(file_result)
            result.destinations_by_index[index] = destination
            _notify(progress_callback, file_result, index, total)
            continue

        destination_name = source.name
        if number_files:
            destination_name = f"{index + 1:0{number_width}d} - {destination_name}"
        destination_name = unique_name(destination_name, used_names)
        used_names.add(destination_name.casefold())
        destination = folder / destination_name

        if destination.exists():
            if destination.resolve() == resolved_source:
                file_result = FileCopyResult(
                    track_title=track.title,
                    source=source,
                    destination=destination,
                    status=CopyStatus.SKIPPED,
                    error="Source and destination are the same file",
                )
            elif overwrite:
                file_result = _copy_file(track.title, source, destination)
            else:
                file_result = FileCopyResult(
                    track_title=track.title,
                    source=source,
                    destination=destination,
                    status=CopyStatus.SKIPPED,
                )
        else:
            file_result = _copy_file(track.title, source, destination)

        result.files.append(file_result)
        if file_result.destination is not None and file_result.status in (
            CopyStatus.COPIED,
            CopyStatus.SKIPPED,
        ):
            result.destinations_by_index[index] = file_result.destination
            if not number_files:
                source_to_destination[resolved_source] = file_result.destination

        _notify(progress_callback, file_result, index, total)

    return result


def _copy_file(track_title: str, source: Path, destination: Path) -> FileCopyResult:
    """Copy one file and convert OSError into a result."""
    try:
        shutil.copy2(source, destination)
        return FileCopyResult(
            track_title=track_title,
            source=source,
            destination=destination,
            status=CopyStatus.COPIED,
        )
    except OSError as exc:
        message = f"Could not copy {source} to {destination}: {exc}"
        logger.error(message)
        return FileCopyResult(
            track_title=track_title,
            source=source,
            destination=destination,
            status=CopyStatus.ERROR,
            error=message,
        )


def _notify(
    callback: Optional[Callable[[FileCopyResult, int, int], None]],
    file_result: FileCopyResult,
    index: int,
    total: int,
) -> None:
    if callback:
        callback(file_result, index + 1, total)
