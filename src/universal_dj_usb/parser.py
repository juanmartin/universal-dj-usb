"""Rekordbox PDB parser using Kaitai Struct."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO

from .models import Track, Playlist, PlaylistTree
from .kaitai.rekordbox_pdb import RekordboxPdb

logger = logging.getLogger(__name__)


class RekordboxParser:
    """Parser for Rekordbox PDB files using Kaitai Struct."""

    def __init__(self, pdb_path: Path):
        """Initialize the parser with a PDB file path."""
        self.pdb_path = pdb_path
        self.pdb_data: Optional[RekordboxPdb] = None
        self._tracks_cache: Dict[int, Track] = {}
        self._playlists_cache: List[Playlist] = []

    def parse(self) -> bool:
        """Parse the PDB file."""
        try:
            with open(self.pdb_path, "rb") as f:
                # Read the entire file into memory
                data = f.read()
                # Create KaitaiStream from the data
                stream = KaitaiStream(BytesIO(data))
                # Parse with Kaitai Struct
                self.pdb_data = RekordboxPdb(False, stream)
            logger.info(f"Successfully parsed PDB file: {self.pdb_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to parse PDB file {self.pdb_path}: {e}")
            return False

    def get_playlists(self) -> PlaylistTree:
        """Extract all playlists from the PDB."""
        if not self.pdb_data and not self.parse():
            return PlaylistTree()

        try:
            # Get playlist metadata
            playlist_metadata = self._extract_playlist_metadata()
            # Get playlist entries (track associations)
            playlist_entries = self._extract_playlist_entries()
            # Get all tracks
            all_tracks = self._extract_tracks()

            # Build playlist objects
            playlists_dict = {}
            root_playlists = []

            for meta in playlist_metadata:
                # Get tracks for this playlist
                track_ids = [
                    entry["track_id"]
                    for entry in playlist_entries
                    if entry["playlist_id"] == meta["id"]
                ]
                tracks = [all_tracks.get(track_id) for track_id in track_ids]
                tracks = [track for track in tracks if track is not None]

                playlist = Playlist(
                    id=meta["id"],
                    name=meta["name"],
                    tracks=tracks,
                    is_folder=meta["is_folder"],
                    parent_id=meta["parent_id"] if meta["parent_id"] != 0 else None,
                )

                playlists_dict[meta["id"]] = playlist

                # Add to root if no parent
                if playlist.parent_id is None:
                    root_playlists.append(playlist)

            return PlaylistTree(
                root_playlists=root_playlists, all_playlists=playlists_dict
            )

        except Exception as e:
            logger.error(f"Error extracting playlists: {e}")
            return PlaylistTree()

    def _extract_playlist_metadata(self) -> List[Dict]:
        """Extract playlist metadata from the playlist tree table."""
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
            try:
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

                            playlist_meta = {
                                "id": playlist_row.id,
                                "name": (
                                    playlist_row.name.body.text
                                    if playlist_row.name and playlist_row.name.body
                                    else ""
                                ),
                                "parent_id": playlist_row.parent_id,
                                "is_folder": playlist_row.is_folder,
                                "sort_order": playlist_row.sort_order,
                            }

                            playlists.append(playlist_meta)

                # Move to next page
                current_page = (
                    page_data.next_page if page_data.next_page.index > 0 else None
                )

            except Exception as e:
                logger.error(f"Error processing playlist page: {e}")
                break

        logger.info(f"Found {len(playlists)} playlists")
        return playlists

    def _extract_playlist_entries(self) -> List[Dict]:
        """Extract playlist entries (track associations) from the PDB."""
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
            try:
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

                            entry = {
                                "playlist_id": entry_row.playlist_id,
                                "track_id": entry_row.track_id,
                                "entry_index": entry_row.entry_index,
                            }

                            entries.append(entry)

                # Move to next page
                current_page = (
                    page_data.next_page if page_data.next_page.index > 0 else None
                )

            except Exception as e:
                logger.error(f"Error processing playlist entries page: {e}")
                break

        logger.info(f"Found {len(entries)} playlist entries")
        return entries

    def _extract_tracks(self) -> Dict[int, Track]:
        """Extract track metadata from the PDB."""
        if self._tracks_cache:
            return self._tracks_cache

        tracks = {}

        # Find the tracks table (type 0)
        tracks_table = None
        for table in self.pdb_data.tables:
            if table.type == RekordboxPdb.PageType.tracks:
                tracks_table = table
                break

        if not tracks_table:
            logger.warning("No tracks table found")
            return {}

        # Parse all pages in the tracks table
        current_page = tracks_table.first_page

        while current_page and current_page.index > 0:
            try:
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
                            track_row = row_ref.body

                            # Extract file path
                            file_path_str = ""
                            if track_row.file_path and track_row.file_path.body:
                                file_path_str = track_row.file_path.body.text

                            # Create Track object
                            track = Track(
                                title=(
                                    track_row.title.body.text
                                    if track_row.title and track_row.title.body
                                    else "Unknown"
                                ),
                                artist="Unknown",  # Artist info is in separate table
                                file_path=(
                                    Path(file_path_str)
                                    if file_path_str
                                    else Path("Unknown")
                                ),
                                album=None,  # Album info is in separate table
                                genre=None,  # Genre info is in separate table
                                year=(
                                    track_row.year
                                    if hasattr(track_row, "year") and track_row.year > 0
                                    else None
                                ),
                                bpm=(
                                    (track_row.tempo / 100.0)
                                    if hasattr(track_row, "tempo")
                                    and track_row.tempo > 0
                                    else None
                                ),
                                duration=(
                                    track_row.duration
                                    if hasattr(track_row, "duration")
                                    and track_row.duration > 0
                                    else None
                                ),
                                bitrate=(
                                    track_row.bitrate
                                    if hasattr(track_row, "bitrate")
                                    and track_row.bitrate > 0
                                    else None
                                ),
                                sample_rate=(
                                    track_row.sample_rate
                                    if hasattr(track_row, "sample_rate")
                                    and track_row.sample_rate > 0
                                    else None
                                ),
                                file_size=(
                                    track_row.file_size
                                    if hasattr(track_row, "file_size")
                                    and track_row.file_size > 0
                                    else None
                                ),
                                rating=(
                                    track_row.rating
                                    if hasattr(track_row, "rating")
                                    and track_row.rating > 0
                                    else None
                                ),
                            )

                            tracks[track_row.id] = track

                # Move to next page
                try:
                    current_page = (
                        page_data.next_page if page_data.next_page.index > 0 else None
                    )
                except Exception as page_error:
                    # This often happens at the end of the table - not necessarily an error
                    logger.debug(f"Reached end of tracks table: {page_error}")
                    break

            except Exception as e:
                # Check if this is a common end-of-data condition
                error_msg = str(e).lower()
                if (
                    "requested" in error_msg
                    and "bytes" in error_msg
                    and "but only" in error_msg
                ):
                    # This is likely a normal end-of-data condition
                    logger.debug(f"Reached end of tracks data: {e}")
                else:
                    # This is an unexpected error
                    logger.error(f"Error processing tracks page: {e}")
                break

        logger.info(f"Found {len(tracks)} tracks")
        self._tracks_cache = tracks
        return tracks

    @staticmethod
    def find_pdb_file(usb_path: Path) -> Optional[Path]:
        """Find the Rekordbox PDB file on a USB drive."""
        potential_paths = [
            usb_path / "PIONEER" / "rekordbox" / "export.pdb",
            usb_path / "Pioneer" / "rekordbox" / "export.pdb",
            usb_path / "pioneer" / "rekordbox" / "export.pdb",
        ]

        for pdb_path in potential_paths:
            if pdb_path.exists():
                logger.info(f"Found PDB file at: {pdb_path}")
                return pdb_path

        logger.error(f"No PDB file found in {usb_path}")
        return None
