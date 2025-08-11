"""Rekordbox PDB parser using Kaitai Struct."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO

from .models import Track, Playlist, PlaylistTree
from .kaitai.rekordbox_pdb import RekordboxPdb
from .metadata_extractor import AudioMetadataExtractor

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

            # Debug: log available tables
            if logger.isEnabledFor(logging.DEBUG):
                self._log_available_tables()

            return True
        except Exception as e:
            logger.error(f"Failed to parse PDB file {self.pdb_path}: {e}")
            return False

    def get_playlists(self, usb_path: Optional[Path] = None) -> PlaylistTree:
        """Extract all playlists from the PDB with minimal track info for performance."""
        if not self.pdb_data and not self.parse():
            return PlaylistTree()

        try:
            # Get playlist metadata
            playlist_metadata = self._extract_playlist_metadata()
            # Get playlist entries (track associations)
            playlist_entries = self._extract_playlist_entries()
            # Get minimal track info only (just IDs and names for listing)
            minimal_tracks = self._extract_minimal_tracks()

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
                tracks = [minimal_tracks.get(track_id) for track_id in track_ids]
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

    def _extract_minimal_tracks(self) -> Dict[int, Track]:
        """Extract minimal track info for playlist listing (IDs, names, paths only)."""
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

        # Parse all pages in the tracks table - but only extract minimal info
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

                            # Extract only minimal info - no metadata lookups
                            file_path_str = ""
                            if track_row.file_path and track_row.file_path.body:
                                file_path_str = track_row.file_path.body.text

                            # Create minimal Track object
                            file_path = (
                                Path(file_path_str)
                                if file_path_str
                                else Path("Unknown")
                            )

                            track = Track(
                                title=(
                                    track_row.title.body.text
                                    if track_row.title and track_row.title.body
                                    else "Unknown"
                                ),
                                artist="Unknown",  # Will be resolved during enhancement if needed
                                file_path=file_path,
                                # Leave other fields as defaults - they'll be filled during enhancement
                            )

                            tracks[track_row.id] = track

                # Move to next page
                try:
                    current_page = (
                        page_data.next_page if page_data.next_page.index > 0 else None
                    )
                except Exception as page_error:
                    logger.debug(f"Reached end of minimal tracks table: {page_error}")
                    break

            except Exception as e:
                # Check if this is a common end-of-data condition
                error_msg = str(e).lower()
                if (
                    "requested" in error_msg
                    and "bytes" in error_msg
                    and "but only" in error_msg
                ):
                    logger.debug(f"Reached end of minimal tracks data: {e}")
                else:
                    logger.error(f"Error processing minimal tracks page: {e}")
                break

        logger.info(f"Found {len(tracks)} tracks (minimal info)")
        return tracks

    def _extract_tracks(self) -> Dict[int, Track]:
        """Extract track metadata from the PDB."""
        if self._tracks_cache:
            return self._tracks_cache

        tracks = {}

        # Extract lookup tables first
        lookup_tables = self._extract_lookup_tables()

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

                            # Create Track object with resolved metadata
                            artist_name = "Unknown"
                            if (
                                hasattr(track_row, "artist_id")
                                and track_row.artist_id > 0
                            ):
                                artist_name = lookup_tables["artists"].get(
                                    track_row.artist_id,
                                    f"Unknown[ID:{track_row.artist_id}]",
                                )
                                # Only log debug for first 5 tracks to avoid spam
                                if len(tracks) < 5:
                                    logger.debug(
                                        f"Track {track_row.id}: artist_id={track_row.artist_id} -> '{artist_name}'"
                                    )

                            album_name = None
                            if (
                                hasattr(track_row, "album_id")
                                and track_row.album_id > 0
                            ):
                                album_name = lookup_tables["albums"].get(
                                    track_row.album_id,
                                    f"Unknown[ID:{track_row.album_id}]",
                                )
                                # Only log debug for first 5 tracks to avoid spam
                                if len(tracks) < 5:
                                    logger.debug(
                                        f"Track {track_row.id}: album_id={track_row.album_id} -> '{album_name}'"
                                    )

                            genre_name = None
                            if (
                                hasattr(track_row, "genre_id")
                                and track_row.genre_id > 0
                            ):
                                genre_name = lookup_tables["genres"].get(
                                    track_row.genre_id,
                                    f"Unknown[ID:{track_row.genre_id}]",
                                )
                                # Only log debug for first 5 tracks to avoid spam
                                if len(tracks) < 5:
                                    logger.debug(
                                        f"Track {track_row.id}: genre_id={track_row.genre_id} -> '{genre_name}'"
                                    )

                            # Create Track object with PDB metadata only (fast)
                            file_path = (
                                Path(file_path_str)
                                if file_path_str
                                else Path("Unknown")
                            )

                            track = Track(
                                title=(
                                    track_row.title.body.text
                                    if track_row.title and track_row.title.body
                                    else "Unknown"
                                ),
                                artist=artist_name,
                                file_path=file_path,
                                album=album_name,
                                genre=genre_name,
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
                                    * 1000  # Convert kbps to bps for Traktor
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

    def _log_available_tables(self) -> None:
        """Log all available tables in the PDB for debugging."""
        logger.debug("Available PDB tables:")
        for table in self.pdb_data.tables:
            logger.debug(
                f"  Table type {table.type.value}: {table.type.name} (first_page: {table.first_page.index})"
            )

    def _extract_lookup_tables(self) -> Dict[str, Dict[int, str]]:
        """Extract lookup tables (artists, albums, genres, etc.) for metadata resolution."""
        lookup_tables = {
            "artists": {},
            "albums": {},
            "genres": {},
            "labels": {},
            "keys": {},
        }

        # Extract artists
        artists_table = None
        for table in self.pdb_data.tables:
            if table.type == RekordboxPdb.PageType.artists:
                artists_table = table
                break

        if artists_table:
            lookup_tables["artists"] = self._extract_string_lookup_table(
                artists_table, "artists"
            )

        # Extract albums
        albums_table = None
        for table in self.pdb_data.tables:
            if table.type == RekordboxPdb.PageType.albums:
                albums_table = table
                break

        if albums_table:
            lookup_tables["albums"] = self._extract_string_lookup_table(
                albums_table, "albums"
            )

        # Extract genres
        genres_table = None
        for table in self.pdb_data.tables:
            if table.type == RekordboxPdb.PageType.genres:
                genres_table = table
                break

        if genres_table:
            lookup_tables["genres"] = self._extract_string_lookup_table(
                genres_table, "genres"
            )

        # Extract labels
        labels_table = None
        for table in self.pdb_data.tables:
            if table.type == RekordboxPdb.PageType.labels:
                labels_table = table
                break

        if labels_table:
            lookup_tables["labels"] = self._extract_string_lookup_table(
                labels_table, "labels"
            )

        # Extract keys
        keys_table = None
        for table in self.pdb_data.tables:
            if table.type == RekordboxPdb.PageType.keys:
                keys_table = table
                break

        if keys_table:
            lookup_tables["keys"] = self._extract_string_lookup_table(
                keys_table, "keys"
            )

        return lookup_tables

    def _extract_string_lookup_table(self, table, table_name: str) -> Dict[int, str]:
        """Extract a string lookup table (artists, albums, genres, etc.)."""
        lookup_dict = {}
        current_page = table.first_page

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
                            row = row_ref.body

                            # All these tables have id and name properties
                            if hasattr(row, "id") and hasattr(row, "name"):
                                name_text = ""
                                if (
                                    row.name
                                    and hasattr(row.name, "body")
                                    and row.name.body
                                ):
                                    name_text = row.name.body.text

                                lookup_dict[row.id] = name_text

                # Move to next page
                current_page = (
                    page_data.next_page if page_data.next_page.index > 0 else None
                )

            except Exception as e:
                logger.debug(f"End of {table_name} table: {e}")
                break

        logger.debug(f"Loaded {len(lookup_dict)} {table_name}")
        return lookup_dict

    def _enhance_tracks_with_file_metadata(
        self, tracks: List[Track], usb_path: Path
    ) -> List[Track]:
        """
        Enhance tracks with file and path metadata only for tracks that are actually used.

        Args:
            tracks: List of Track objects to enhance
            usb_path: Path to the USB drive

        Returns:
            List of enhanced Track objects
        """
        enhanced_tracks = []

        for track in tracks:
            try:
                # Prepare PDB metadata from existing track
                pdb_metadata = {
                    "title": track.title if track.title != "Unknown" else None,
                    "artist": track.artist if track.artist != "Unknown" else None,
                    "album": (
                        track.album
                        if track.album and not track.album.startswith("Unknown[ID:")
                        else None
                    ),
                    "genre": track.genre,
                    "year": track.year,
                    "bpm": track.bpm,
                    "duration": track.duration,
                    "bitrate": track.bitrate,
                    "sample_rate": track.sample_rate,
                    "comment": track.comment,
                }

                # Extract metadata from file path
                path_metadata = AudioMetadataExtractor.extract_metadata_from_path(
                    track.file_path
                )

                # Extract metadata from audio file
                file_metadata = {}
                if str(track.file_path) != "Unknown":
                    try:
                        # Remove leading slash if present
                        clean_path = str(track.file_path).lstrip("/")
                        full_file_path = usb_path / clean_path
                        file_metadata = (
                            AudioMetadataExtractor.extract_metadata_from_file(
                                full_file_path
                            )
                        )
                    except Exception as e:
                        logger.debug(
                            f"Could not extract file metadata for {track.file_path}: {e}"
                        )

                # Merge all metadata sources
                merged_metadata = AudioMetadataExtractor.merge_metadata(
                    pdb_metadata, file_metadata, path_metadata
                )

                # Create enhanced track
                enhanced_track = Track(
                    title=merged_metadata.get("title", "Unknown"),
                    artist=merged_metadata.get("artist", "Unknown"),
                    file_path=track.file_path,
                    album=merged_metadata.get("album"),
                    genre=merged_metadata.get("genre"),
                    year=merged_metadata.get("year"),
                    bpm=merged_metadata.get("bpm"),
                    duration=merged_metadata.get("duration"),
                    bitrate=merged_metadata.get("bitrate"),
                    sample_rate=merged_metadata.get("sample_rate"),
                    file_size=track.file_size,
                    rating=track.rating,
                    comment=merged_metadata.get("comment"),
                    cue_points=track.cue_points,
                )

                enhanced_tracks.append(enhanced_track)

            except Exception as e:
                logger.warning(f"Error enhancing track {track.title}: {e}")
                # Use original track if enhancement fails
                enhanced_tracks.append(track)

        return enhanced_tracks

    def enhance_playlist_tracks(self, playlist: Playlist, usb_path: Path) -> Playlist:
        """
        Enhance a specific playlist's tracks with full PDB metadata and file metadata.

        Args:
            playlist: Playlist object to enhance
            usb_path: Path to the USB drive

        Returns:
            Playlist with enhanced tracks
        """
        if not usb_path:
            return playlist

        logger.info(
            f"Enhancing {len(playlist.tracks)} tracks for playlist '{playlist.name}'"
        )

        # Extract full metadata only for tracks in this playlist
        track_ids = [
            track.file_path.stem for track in playlist.tracks if track.file_path
        ]
        enhanced_tracks = self._extract_specific_tracks_full_metadata(
            track_ids, playlist.tracks
        )

        # Further enhance with file system metadata
        final_tracks = self._enhance_tracks_with_file_metadata(
            enhanced_tracks, usb_path
        )

        # Create new playlist with enhanced tracks
        return Playlist(
            id=playlist.id,
            name=playlist.name,
            tracks=final_tracks,
            is_folder=playlist.is_folder,
            parent_id=playlist.parent_id,
        )

    def _extract_specific_tracks_full_metadata(
        self, track_ids: List[str], minimal_tracks: List[Track]
    ) -> List[Track]:
        """
        Extract full PDB metadata only for specific tracks.

        Args:
            track_ids: List of track identifiers to enhance
            minimal_tracks: List of minimal track objects

        Returns:
            List of enhanced Track objects with full PDB metadata
        """
        if not minimal_tracks:
            return []

        # Create mapping from file paths to minimal tracks
        track_by_path = {}
        for track in minimal_tracks:
            if track.file_path:
                track_by_path[str(track.file_path)] = track

        enhanced_tracks = []

        # Extract lookup tables (only if we need to enhance tracks)
        lookup_tables = self._extract_lookup_tables()

        # Find the tracks table (type 0)
        tracks_table = None
        for table in self.pdb_data.tables:
            if table.type == RekordboxPdb.PageType.tracks:
                tracks_table = table
                break

        if not tracks_table:
            logger.warning("No tracks table found for enhancement")
            return minimal_tracks

        # Parse tracks table looking for our specific tracks
        current_page = tracks_table.first_page
        found_tracks = 0
        target_count = len(minimal_tracks)

        while current_page and current_page.index > 0 and found_tracks < target_count:
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

                            # Check if this track is in our target list
                            if file_path_str and file_path_str in track_by_path:
                                # Create enhanced Track object with full metadata
                                artist_name = "Unknown"
                                if (
                                    hasattr(track_row, "artist_id")
                                    and track_row.artist_id > 0
                                ):
                                    artist_name = lookup_tables["artists"].get(
                                        track_row.artist_id,
                                        f"Unknown[ID:{track_row.artist_id}]",
                                    )

                                album_name = None
                                if (
                                    hasattr(track_row, "album_id")
                                    and track_row.album_id > 0
                                ):
                                    album_name = lookup_tables["albums"].get(
                                        track_row.album_id,
                                        f"Unknown[ID:{track_row.album_id}]",
                                    )

                                genre_name = None
                                if (
                                    hasattr(track_row, "genre_id")
                                    and track_row.genre_id > 0
                                ):
                                    genre_name = lookup_tables["genres"].get(
                                        track_row.genre_id,
                                        f"Unknown[ID:{track_row.genre_id}]",
                                    )

                                file_path = Path(file_path_str)

                                enhanced_track = Track(
                                    title=(
                                        track_row.title.body.text
                                        if track_row.title and track_row.title.body
                                        else "Unknown"
                                    ),
                                    artist=artist_name,
                                    file_path=file_path,
                                    album=album_name,
                                    genre=genre_name,
                                    year=(
                                        track_row.year
                                        if hasattr(track_row, "year")
                                        and track_row.year > 0
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
                                        track_row.bitrate * 1000  # Convert kbps to bps
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

                                enhanced_tracks.append(enhanced_track)
                                found_tracks += 1

                # Move to next page
                try:
                    current_page = (
                        page_data.next_page if page_data.next_page.index > 0 else None
                    )
                except Exception as page_error:
                    logger.debug(
                        f"Reached end of tracks table during enhancement: {page_error}"
                    )
                    break

            except Exception as e:
                error_msg = str(e).lower()
                if (
                    "requested" in error_msg
                    and "bytes" in error_msg
                    and "but only" in error_msg
                ):
                    logger.debug(f"Reached end of tracks data during enhancement: {e}")
                else:
                    logger.error(
                        f"Error processing tracks page during enhancement: {e}"
                    )
                break

        logger.debug(f"Enhanced {len(enhanced_tracks)} tracks with full PDB metadata")

        # If we didn't find all tracks, include the ones we did find plus any minimal ones we missed
        if len(enhanced_tracks) < len(minimal_tracks):
            enhanced_paths = {str(track.file_path) for track in enhanced_tracks}
            for minimal_track in minimal_tracks:
                if str(minimal_track.file_path) not in enhanced_paths:
                    enhanced_tracks.append(minimal_track)

        return enhanced_tracks
