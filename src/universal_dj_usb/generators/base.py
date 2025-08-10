"""Base generator class for playlist format conversion."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from ..models import Playlist, ConversionConfig, ConversionResult


class BaseGenerator(ABC):
    """Base class for playlist format generators."""

    def __init__(self, config: ConversionConfig):
        """Initialize the generator with configuration."""
        self.config = config

    @abstractmethod
    def generate(
        self, playlist: Playlist, output_path: Path, usb_path: Path = None
    ) -> ConversionResult:
        """Generate a playlist file in the specific format."""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this format."""
        pass

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a filename for cross-platform compatibility."""
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "_")

        # Trim whitespace and dots
        name = name.strip().strip(".")

        # Ensure it's not empty
        if not name:
            name = "playlist"

        return name

    def _normalize_path(self, path: Path, base_path: Path = None) -> str:
        """Normalize file path for cross-platform compatibility."""
        if base_path and self.config.relative_paths:
            try:
                rel_path = path.relative_to(base_path)
                return str(rel_path).replace("\\", "/")
            except ValueError:
                # Fallback to absolute path if relative fails
                pass
        return str(path).replace("\\", "/")
