"""Utility functions for path handling, USB detection, and file operations."""

import os
import platform
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import re

logger = logging.getLogger(__name__)


def detect_usb_drives() -> List[Path]:
    """
    Detect USB drives that might contain Rekordbox exports.

    Returns:
        List of Path objects representing potential USB drives.
    """
    usb_drives = []
    system = platform.system()

    if system == "Windows":
        # Check all drive letters
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive_path = Path(f"{letter}:\\")
            if drive_path.exists() and _is_removable_drive(drive_path):
                if _has_rekordbox_export(drive_path):
                    usb_drives.append(drive_path)

    elif system == "Darwin":  # macOS
        # Check /Volumes for mounted drives
        volumes_path = Path("/Volumes")
        if volumes_path.exists():
            for volume in volumes_path.iterdir():
                if volume.is_dir() and volume.name != "Macintosh HD":
                    if _has_rekordbox_export(volume):
                        usb_drives.append(volume)

    elif system == "Linux":
        # Check common mount points
        mount_points = ["/media", "/mnt", "/run/media"]
        for mount_point in mount_points:
            mount_path = Path(mount_point)
            if mount_path.exists():
                # Check user-specific directories
                for user_dir in mount_path.iterdir():
                    if user_dir.is_dir():
                        for volume in user_dir.iterdir():
                            if volume.is_dir() and _has_rekordbox_export(volume):
                                usb_drives.append(volume)

                # Also check direct mounts
                for volume in mount_path.iterdir():
                    if volume.is_dir() and _has_rekordbox_export(volume):
                        usb_drives.append(volume)

    return usb_drives


def _is_removable_drive(drive_path: Path) -> bool:
    """Check if a drive is removable (Windows only)."""
    try:
        import win32file

        drive_type = win32file.GetDriveType(str(drive_path))
        return drive_type == win32file.DRIVE_REMOVABLE
    except ImportError:
        # If win32file is not available, assume it's removable
        return True
    except Exception:
        return False


def _has_rekordbox_export(drive_path: Path) -> bool:
    """Check if a drive contains a Rekordbox export."""
    pioneer_path = drive_path / "PIONEER"
    if not pioneer_path.exists():
        return False

    export_path = pioneer_path / "rekordbox" / "export.pdb"
    return export_path.exists()


def normalize_path(
    path: Path, base_path: Optional[Path] = None, use_relative: bool = True
) -> str:
    """
    Normalize a file path for cross-platform compatibility.

    Args:
        path: The path to normalize
        base_path: Base path for relative path calculation
        use_relative: Whether to use relative paths

    Returns:
        Normalized path string with forward slashes
    """
    if use_relative and base_path:
        try:
            # Convert to relative path
            rel_path = path.relative_to(base_path)
            return str(rel_path).replace("\\", "/")
        except ValueError:
            # If path is not relative to base_path, use absolute path
            pass

    # Use absolute path, but normalize slashes
    return str(path).replace("\\", "/")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to be safe for all operating systems.

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, "_", filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip(" .")

    # Ensure it's not empty
    if not filename:
        filename = "unnamed"

    # Limit length
    if len(filename) > 200:
        filename = filename[:200]

    return filename


def get_file_size(file_path: Path) -> Optional[int]:
    """
    Get the size of a file in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes or None if file doesn't exist
    """
    try:
        return file_path.stat().st_size
    except (OSError, FileNotFoundError):
        return None


def create_directory(dir_path: Path) -> bool:
    """
    Create a directory if it doesn't exist.

    Args:
        dir_path: Path to the directory to create

    Returns:
        True if directory was created or already exists, False otherwise
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        return False


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from a TOML file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Configuration dictionary
    """
    try:
        import toml

        with open(config_path, "r") as f:
            return toml.load(f)
    except (ImportError, FileNotFoundError, Exception) as e:
        logger.warning(f"Failed to load config from {config_path}: {e}")
        return {}


def save_config(config: Dict[str, Any], config_path: Path) -> bool:
    """
    Save configuration to a TOML file.

    Args:
        config: Configuration dictionary
        config_path: Path to save the configuration file

    Returns:
        True if successful, False otherwise
    """
    try:
        import toml

        create_directory(config_path.parent)
        with open(config_path, "w") as f:
            toml.dump(config, f)
        return True
    except (ImportError, Exception) as e:
        logger.error(f"Failed to save config to {config_path}: {e}")
        return False


def validate_rekordbox_export(export_path: Path) -> bool:
    """
    Validate that a path contains a valid Rekordbox export.

    Args:
        export_path: Path to the export.pdb file

    Returns:
        True if valid, False otherwise
    """
    if not export_path.exists():
        return False

    if not export_path.is_file():
        return False

    if export_path.suffix.lower() != ".pdb":
        return False

    # Check if file is readable and has reasonable size
    try:
        size = export_path.stat().st_size
        if size < 100:  # Too small to be a valid PDB
            return False
        if size > 1024 * 1024 * 100:  # Larger than 100MB is suspicious
            logger.warning(f"PDB file is unusually large: {size} bytes")
    except OSError:
        return False

    return True


def get_platform_specific_paths() -> Dict[str, Path]:
    """
    Get platform-specific paths for configuration and data.

    Returns:
        Dictionary with 'config' and 'data' paths
    """
    system = platform.system()
    home = Path.home()

    if system == "Windows":
        config_dir = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        data_dir = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
    elif system == "Darwin":  # macOS
        config_dir = home / "Library" / "Application Support"
        data_dir = home / "Library" / "Application Support"
    else:  # Linux and others
        config_dir = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
        data_dir = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))

    app_name = "universal-dj-usb"

    return {"config": config_dir / app_name, "data": data_dir / app_name}


def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None) -> None:
    """
    Set up logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional path to log file
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]
    if log_file:
        create_directory(log_file.parent)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


def estimate_conversion_time(track_count: int) -> float:
    """
    Estimate conversion time based on track count.

    Args:
        track_count: Number of tracks to convert

    Returns:
        Estimated time in seconds
    """
    # Rough estimate: 0.1 seconds per track
    return track_count * 0.1
