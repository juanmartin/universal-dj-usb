"""Rekordbox PDB parser using Kaitai Struct for accurate playlist-track associations."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .pdb_parser.rekordbox_pdb import RekordboxPdb
from .models import Track, Playlist, PlaylistTree

logger = logging.getLogger(__name__)


@dataclass
class PlaylistEntry:
    """Represents a playlist entry with track association."""

    playlist_id: int
    track_id: int
    entry_index: int


@dataclass
class PlaylistMetadata:
    """Represents playlist metadata."""

    id: int
    name: str
    parent_id: int
    is_folder: bool
    sort_order: int


@dataclass
class TrackMetadata:
    """Represents track metadata from the PDB."""

    id: int
    title: str
    artist: str
    album: str
    file_path: str
    filename: str
    duration: Optional[int] = None
    bpm: Optional[float] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    file_size: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    key: Optional[str] = None
    rating: Optional[int] = None
    play_count: Optional[int] = None


class AdvancedPDBParser:
    """Advanced PDB parser using Kaitai Struct definitions."""

    def __init__(self, pdb_path: Path, usb_path: Path):
        """Initialize the parser with paths."""
        self.pdb_path = pdb_path
        self.usb_path = usb_path
        self.pdb_data = None
        self._playlists_cache = None
        self._tracks_cache = None
        self._playlist_entries_cache = None

    def parse(self) -> bool:
        """Parse the PDB file and load data."""
        try:
            logger.info(f"Parsing PDB file: {self.pdb_path}")

            # Read the entire file into memory to avoid file handle issues
            with open(self.pdb_path, "rb") as f:
                file_data = f.read()

            # Create a BytesIO stream from the file data
            from kaitaistruct import KaitaiStream
            from io import BytesIO

            stream = KaitaiStream(BytesIO(file_data))
            self.pdb_data = RekordboxPdb(is_ext=False, _io=stream)

            logger.info(
                f"Successfully parsed PDB with {len(self.pdb_data.tables)} tables"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to parse PDB file: {e}")
            return False

    def get_playlists(self) -> List[PlaylistMetadata]:
        """Extract playlist metadata from the PDB."""
        if self._playlists_cache is not None:
            return self._playlists_cache

        # Ensure PDB data is parsed
        if self.pdb_data is None:
            if not self.parse():
                logger.error("Failed to parse PDB file")
                return []

        playlists = []

        # Find the playlist tree table (type 7)
        playlist_tree_table = None
        for table in self.pdb_data.tables:
            if table.type == RekordboxPdb.PageType.playlist_tree:
                playlist_tree_table = table
                break

        if not playlist_tree_table:
            logger.warning("No playlist tree table found")
            return []

        # Parse all pages in the playlist tree table
        current_page = playlist_tree_table.first_page

        while current_page and current_page.index > 0:
            page_data = current_page.body

            if not page_data.is_data_page:
                current_page = (
                    page_data.next_page if page_data.next_page.index > 0 else None
                )
                continue

            # Process all row groups in this page
            for row_group in page_data.row_groups:
                for row_ref in row_group.rows:
                    if row_ref.present and row_ref.body:
                        playlist_row = row_ref.body

                        # Extract playlist metadata
                        playlist_meta = PlaylistMetadata(
                            id=playlist_row.id,
                            name=(
                                playlist_row.name.body.text
                                if playlist_row.name.body
                                else ""
                            ),
                            parent_id=playlist_row.parent_id,
                            is_folder=playlist_row.is_folder,
                            sort_order=playlist_row.sort_order,
                        )

                        playlists.append(playlist_meta)

            # Move to next page
            current_page = (
                page_data.next_page if page_data.next_page.index > 0 else None
            )

        logger.info(f"Found {len(playlists)} playlists")
        self._playlists_cache = playlists
        return playlists

    def get_tracks(self) -> List[TrackMetadata]:
        """Extract track metadata from the PDB."""
        if self._tracks_cache is not None:
            return self._tracks_cache

        # Ensure PDB data is parsed
        if self.pdb_data is None:
            if not self.parse():
                logger.error("Failed to parse PDB file")
                return []

        tracks = []

        # Find the tracks table (type 0)
        tracks_table = None
        for table in self.pdb_data.tables:
            if table.type == RekordboxPdb.PageType.tracks:
                tracks_table = table
                break

        if not tracks_table:
            logger.warning("No tracks table found")
            return []

        logger.info(
            f"Starting track parsing from table with first page index: {tracks_table.first_page.index}"
        )

        # Parse all pages in the tracks table
        current_page = tracks_table.first_page
        page_count = 0

        try:
            while current_page and current_page.index > 0:
                page_count += 1
                logger.debug(
                    f"Processing tracks page {page_count} (index: {current_page.index})"
                )

                try:
                    page_data = current_page.body
                except Exception as e:
                    logger.error(f"Failed to read page {current_page.index} body: {e}")
                    break

                if not page_data.is_data_page:
                    logger.debug(
                        f"Page {current_page.index} is not a data page, skipping"
                    )
                    current_page = (
                        page_data.next_page if page_data.next_page.index > 0 else None
                    )
                    continue

                # Process all row groups in this page
                try:
                    for row_group_idx, row_group in enumerate(page_data.row_groups):
                        for row_idx, row_ref in enumerate(row_group.rows):
                            if row_ref.present and row_ref.body:
                                try:
                                    track_row = row_ref.body

                                    # Extract track metadata
                                    track_meta = TrackMetadata(
                                        id=track_row.id,
                                        title=(
                                            track_row.title.body.text
                                            if track_row.title.body
                                            else ""
                                        ),
                                        artist="",  # Will be populated from artist table lookup
                                        album="",  # Will be populated from album table lookup
                                        file_path=(
                                            track_row.file_path.body.text
                                            if track_row.file_path.body
                                            else ""
                                        ),
                                        filename=(
                                            track_row.filename.body.text
                                            if track_row.filename.body
                                            else ""
                                        ),
                                        duration=track_row.duration,
                                        bpm=(
                                            track_row.tempo / 100.0
                                            if track_row.tempo
                                            else None
                                        ),
                                        bitrate=track_row.bitrate,
                                        sample_rate=track_row.sample_rate,
                                        file_size=track_row.file_size,
                                        year=track_row.year,
                                        rating=track_row.rating,
                                        play_count=track_row.play_count,
                                    )

                                    tracks.append(track_meta)

                                except Exception as e:
                                    logger.error(
                                        f"Failed to parse track row {row_idx} in group {row_group_idx} on page {current_page.index}: {e}"
                                    )
                                    # Continue with next row instead of breaking
                                    continue

                except Exception as e:
                    logger.error(
                        f"Failed to process row groups on page {current_page.index}: {e}"
                    )
                    break

                # Move to next page
                try:
                    current_page = (
                        page_data.next_page if page_data.next_page.index > 0 else None
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to get next page from page {current_page.index}: {e}"
                    )
                    break

        except Exception as e:
            logger.error(f"Critical error during track parsing: {e}")
            logger.info(f"Parsed {len(tracks)} tracks before error")

        logger.info(f"Found {len(tracks)} tracks after processing {page_count} pages")
        self._tracks_cache = tracks
        return tracks

    def get_playlist_entries(self) -> List[PlaylistEntry]:
        """Extract playlist entries (track associations) from the PDB."""
        if self._playlist_entries_cache is not None:
            return self._playlist_entries_cache

        # Ensure PDB data is parsed
        if self.pdb_data is None:
            if not self.parse():
                logger.error("Failed to parse PDB file")
                return []

        entries = []

        # Find the playlist entries table (type 8)
        playlist_entries_table = None
        for table in self.pdb_data.tables:
            if table.type == RekordboxPdb.PageType.playlist_entries:
                playlist_entries_table = table
                break

        if not playlist_entries_table:
            logger.warning("No playlist entries table found")
            return []

        # Parse all pages in the playlist entries table
        current_page = playlist_entries_table.first_page

        while current_page and current_page.index > 0:
            page_data = current_page.body

            if not page_data.is_data_page:
                current_page = (
                    page_data.next_page if page_data.next_page.index > 0 else None
                )
                continue

            # Process all row groups in this page
            for row_group in page_data.row_groups:
                for row_ref in row_group.rows:
                    if row_ref.present and row_ref.body:
                        entry_row = row_ref.body

                        # Extract playlist entry
                        entry = PlaylistEntry(
                            playlist_id=entry_row.playlist_id,
                            track_id=entry_row.track_id,
                            entry_index=entry_row.entry_index,
                        )

                        entries.append(entry)

            # Move to next page
            current_page = (
                page_data.next_page if page_data.next_page.index > 0 else None
            )

        logger.info(f"Found {len(entries)} playlist entries")
        self._playlist_entries_cache = entries
        return entries

    def get_tracks_for_playlist(self, playlist_name: str) -> List[TrackMetadata]:
        """Get all tracks for a specific playlist."""
        # Get all data
        playlists = self.get_playlists()
        tracks = self.get_tracks()
        entries = self.get_playlist_entries()

        # Find the playlist by name
        target_playlist = None
        for playlist in playlists:
            if playlist.name.upper() == playlist_name.upper():
                target_playlist = playlist
                break

        if not target_playlist:
            logger.warning(f"Playlist '{playlist_name}' not found")
            return []

        # Get entries for this playlist
        playlist_entries = [
            entry for entry in entries if entry.playlist_id == target_playlist.id
        ]

        # Sort entries by index
        playlist_entries.sort(key=lambda e: e.entry_index)

        # Create tracks lookup
        tracks_lookup = {track.id: track for track in tracks}

        # Get tracks for this playlist
        playlist_tracks = []
        for entry in playlist_entries:
            if entry.track_id in tracks_lookup:
                playlist_tracks.append(tracks_lookup[entry.track_id])

        logger.info(
            f"Found {len(playlist_tracks)} tracks for playlist '{playlist_name}'"
        )
        return playlist_tracks

    def build_playlist_tree(self) -> PlaylistTree:
        """Build a complete playlist tree with actual track associations."""
        playlists = self.get_playlists()
        entries = self.get_playlist_entries()
        tracks = self.get_tracks()

        # Create tracks lookup
        tracks_lookup = {track.id: track for track in tracks}

        # Group entries by playlist
        playlist_entries_map = {}
        for entry in entries:
            if entry.playlist_id not in playlist_entries_map:
                playlist_entries_map[entry.playlist_id] = []
            playlist_entries_map[entry.playlist_id].append(entry)

        # Sort entries within each playlist
        for playlist_id in playlist_entries_map:
            playlist_entries_map[playlist_id].sort(key=lambda e: e.entry_index)

        # Build playlist objects
        all_playlists = {}
        root_playlists = []

        for playlist_meta in playlists:
            # Get tracks for this playlist
            playlist_tracks = []
            if playlist_meta.id in playlist_entries_map:
                for entry in playlist_entries_map[playlist_meta.id]:
                    if entry.track_id in tracks_lookup:
                        track_meta = tracks_lookup[entry.track_id]

                        # Convert to Track object
                        track = Track(
                            title=track_meta.title,
                            artist=track_meta.artist or "Unknown Artist",
                            album=track_meta.album or "Unknown Album",
                            file_path=self.usb_path / track_meta.file_path.lstrip("/"),
                            filename=track_meta.filename,
                            duration=track_meta.duration,
                            bpm=track_meta.bpm,
                            bitrate=track_meta.bitrate,
                            sample_rate=track_meta.sample_rate,
                            file_size=track_meta.file_size,
                            year=track_meta.year,
                            rating=track_meta.rating,
                            play_count=track_meta.play_count,
                        )

                        playlist_tracks.append(track)

            # Create playlist object
            playlist = Playlist(
                name=playlist_meta.name,
                tracks=playlist_tracks,
                is_folder=playlist_meta.is_folder,
                id=playlist_meta.id,
            )

            all_playlists[playlist_meta.id] = playlist

            # Add to root if no parent
            if playlist_meta.parent_id == 0:
                root_playlists.append(playlist)

        return PlaylistTree(root_playlists=root_playlists, all_playlists=all_playlists)

    def export_playlist_to_txt(self, playlist_name: str, output_file: Path) -> bool:
        """Export a playlist to a simple text file for manual verification."""
        try:
            # Get all playlists and find the target playlist
            playlists = self.get_playlists()
            target_playlist = None

            for playlist in playlists:
                if playlist.name == playlist_name:
                    target_playlist = playlist
                    break

            if not target_playlist:
                logger.error(f"Playlist '{playlist_name}' not found")
                return False

            # Get tracks for this playlist
            playlist_tracks = self.get_tracks_for_playlist(playlist_name)

            # Write playlist to text file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"Playlist: {playlist_name}\n")
                f.write(f"Total tracks: {len(playlist_tracks)}\n")
                f.write("=" * 50 + "\n\n")

                for i, track in enumerate(playlist_tracks, 1):
                    f.write(f"{i:3d}. {track.title} - {track.artist}\n")
                    f.write(f"      File: {track.filename}\n")
                    f.write(f"      Path: {track.file_path}\n")
                    f.write(
                        f"      Duration: {track.duration}s, BPM: {track.bpm}\n"
                    )
                    f.write("\n")

            logger.info(f"Playlist '{playlist_name}' exported to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export playlist '{playlist_name}': {e}")
            return False
