"""Path helpers shared by the parser, generators, and playlist copier."""

import platform
from pathlib import Path
from typing import Optional


def sanitize_filename(name: str) -> str:
    """Sanitize a name for cross-platform use as a file or folder name."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")

    name = name.strip().strip(".")
    return name or "playlist"


def unique_name(name: str, used_names: set[str]) -> str:
    """Return a case-insensitively unique name, adding `` (2)`` when needed."""
    if name.casefold() not in used_names:
        return name

    path = Path(name)
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = f"{stem} ({counter}){suffix}"
        if candidate.casefold() not in used_names:
            return candidate
        counter += 1


def resolve_track_source(file_path: Path, usb_path: Optional[Path] = None) -> Path:
    """Resolve a Rekordbox track path to a file on the current machine.

    PDB exports normally store paths such as ``/Contents/Artist/Album/track.mp3``.
    They may also contain absolute paths from the machine that created the database.
    Prefer a path that exists, then fall back to joining the USB root.
    """
    raw = str(file_path).strip()
    if not raw or raw == "Unknown":
        return Path(raw or "Unknown")

    direct = Path(raw)
    if direct.is_absolute() and direct.exists():
        return direct

    if usb_path is None:
        return direct
    # Normalize Windows separators so the same logic works on every host.
    normalized = raw.replace("\\", "/")

    # A path from another machine may still contain the Rekordbox Contents folder.
    # Re-anchor it at the USB root and try again.
    lower = normalized.lower()
    marker_index = lower.find("contents/")
    has_contents_marker = marker_index != -1 and (
        marker_index == 0 or lower[marker_index - 1] == "/"
    )
    if has_contents_marker:
        candidate = usb_path / normalized[marker_index:]
        if candidate.exists():
            return candidate

    stripped = normalized.lstrip("/")
    if len(stripped) >= 2 and stripped[1] == ":":
        stripped = stripped[2:].lstrip("/")

    candidates = [usb_path / stripped]
    if not stripped.lower().startswith("contents/"):
        candidates.append(usb_path / "Contents" / stripped)
    candidates.append(usb_path / Path(normalized).name)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # An absolute path without a Contents marker is likely a real path from
    # this machine that is merely missing. Preserve it for useful errors.
    if direct.is_absolute() and not has_contents_marker:
        return direct

    # Nothing exists. Return the most likely USB location for error reporting.
    return candidates[0]


def relative_path_if_inside(path: Path, base_dir: Path) -> Optional[str]:
    """Return a forward-slash relative path if *path* is inside *base_dir*."""
    try:
        return path.resolve().relative_to(base_dir.resolve()).as_posix()
    except (OSError, ValueError):
        return None


def volume_name_for(path: Path) -> str:
    """Return the volume/drive label Traktor should use for a path."""
    if platform.system() == "Windows":
        return path.anchor.rstrip("\\/")
    return path.name
