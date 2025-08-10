"""Data models for playlist and track information."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
from enum import Enum


class KeySignature(Enum):
    """Musical key signatures."""

    C_MAJOR = "C"
    D_FLAT_MAJOR = "Db"
    D_MAJOR = "D"
    E_FLAT_MAJOR = "Eb"
    E_MAJOR = "E"
    F_MAJOR = "F"
    F_SHARP_MAJOR = "F#"
    G_MAJOR = "G"
    A_FLAT_MAJOR = "Ab"
    A_MAJOR = "A"
    B_FLAT_MAJOR = "Bb"
    B_MAJOR = "B"
    A_MINOR = "Am"
    B_FLAT_MINOR = "Bbm"
    B_MINOR = "Bm"
    C_MINOR = "Cm"
    C_SHARP_MINOR = "C#m"
    D_MINOR = "Dm"
    E_FLAT_MINOR = "Ebm"
    E_MINOR = "Em"
    F_MINOR = "Fm"
    F_SHARP_MINOR = "F#m"
    G_MINOR = "Gm"
    G_SHARP_MINOR = "G#m"


@dataclass
class CuePoint:
    """Represents a cue point in a track."""

    name: str
    position: float  # Position in seconds
    color: Optional[str] = None
    type: str = "CUE"  # CUE or LOOP
    loop_length: Optional[float] = None  # For loop type cues


@dataclass
class Track:
    """Represents a music track with metadata."""

    title: str
    artist: str
    file_path: Path
    album: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    bpm: Optional[float] = None
    key: Optional[KeySignature] = None
    duration: Optional[float] = None  # Duration in seconds
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    file_size: Optional[int] = None
    date_added: Optional[str] = None
    rating: Optional[int] = None  # 0-5 stars
    comment: Optional[str] = None
    cue_points: List[CuePoint] = field(default_factory=list)

    @property
    def relative_path(self) -> str:
        """Get the relative path for cross-platform compatibility."""
        return str(self.file_path).replace("\\", "/")

    @property
    def filename(self) -> str:
        """Get just the filename."""
        return self.file_path.name


@dataclass
class Playlist:
    """Represents a playlist with tracks."""

    name: str
    tracks: List[Track] = field(default_factory=list)
    is_folder: bool = False
    parent_id: Optional[int] = None
    id: Optional[int] = None

    @property
    def track_count(self) -> int:
        """Get the number of tracks in the playlist."""
        return len(self.tracks)

    @property
    def total_duration(self) -> float:
        """Get the total duration of all tracks in seconds."""
        return sum(track.duration or 0 for track in self.tracks)

    def add_track(self, track: Track) -> None:
        """Add a track to the playlist."""
        self.tracks.append(track)

    def remove_track(self, track: Track) -> None:
        """Remove a track from the playlist."""
        if track in self.tracks:
            self.tracks.remove(track)


@dataclass
class PlaylistTree:
    """Represents the hierarchical structure of playlists."""

    root_playlists: List[Playlist] = field(default_factory=list)
    all_playlists: Dict[int, Playlist] = field(default_factory=dict)

    def get_playlist_by_id(self, playlist_id: int) -> Optional[Playlist]:
        """Get a playlist by its ID."""
        return self.all_playlists.get(playlist_id)

    def get_playlist_by_name(self, name: str) -> Optional[Playlist]:
        """Get a playlist by its name."""
        for playlist in self.all_playlists.values():
            if playlist.name == name:
                return playlist
        return None

    def get_child_playlists(self, parent_id: int) -> List[Playlist]:
        """Get all child playlists of a given parent."""
        return [
            playlist
            for playlist in self.all_playlists.values()
            if playlist.parent_id == parent_id
        ]


@dataclass
class ConversionConfig:
    """Configuration for playlist conversion."""

    relative_paths: bool = True
    preserve_folder_structure: bool = True
    include_cue_points: bool = True
    include_loops: bool = True
    file_naming: str = "playlist_name"  # or "sequential"
    encoding: str = "utf-8"
    output_format: str = "nml"  # nml, m3u, m3u8, or all

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ConversionConfig":
        """Create configuration from dictionary."""
        return cls(**{k: v for k, v in config_dict.items() if hasattr(cls, k)})


@dataclass
class ConversionResult:
    """Result of a playlist conversion operation."""

    success: bool
    playlist_name: str
    output_file: Optional[Path] = None
    track_count: int = 0
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
