"""Base generator class for playlist format conversion."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..models import ConversionConfig, ConversionResult, Playlist
from ..paths import relative_path_between, relative_path_if_inside, sanitize_filename


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
        return sanitize_filename(name)

    def _normalize_path(
        self,
        path: Path,
        base_dir: Optional[Path] = None,
        root_dir: Optional[Path] = None,
    ) -> str:
        """Normalize a path for cross-platform playlist output.

        Relative paths are emitted only when *path* is inside *base_dir*. When
        *root_dir* is supplied, a parent-relative path is allowed as long as
        both the track and the playlist directory are inside that root.
        """
        if base_dir and self.config.relative_paths:
            rel_path = relative_path_if_inside(path, base_dir)
            if rel_path is not None:
                return rel_path
            if root_dir is not None:
                rel_path = relative_path_between(path, base_dir, root_dir)
                if rel_path is not None:
                    return rel_path
        return str(path).replace("\\", "/")
