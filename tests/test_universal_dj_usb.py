"""Tests for the Universal DJ USB playlist converter."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from universal_dj_usb.models import (
    Track,
    Playlist,
    CuePoint,
    ConversionConfig,
    ConversionResult,
)
from universal_dj_usb.converter import RekordboxToTraktorConverter
from universal_dj_usb.utils import normalize_path, sanitize_filename


class TestModels:
    """Test the data models."""

    def test_track_creation(self):
        """Test creating a track."""
        track = Track(
            title="Test Song",
            artist="Test Artist",
            file_path=Path("/music/test.mp3"),
            album="Test Album",
            bpm=128.0,
        )

        assert track.title == "Test Song"
        assert track.artist == "Test Artist"
        assert track.bpm == 128.0
        assert track.filename == "test.mp3"
        assert track.relative_path == "/music/test.mp3"

    def test_playlist_creation(self):
        """Test creating a playlist."""
        track1 = Track("Song 1", "Artist 1", Path("/music/song1.mp3"))
        track2 = Track("Song 2", "Artist 2", Path("/music/song2.mp3"))

        playlist = Playlist(name="Test Playlist", tracks=[track1, track2])

        assert playlist.name == "Test Playlist"
        assert playlist.track_count == 2
        assert len(playlist.tracks) == 2

    def test_cue_point_creation(self):
        """Test creating a cue point."""
        cue = CuePoint(name="Drop", position=60.5, color="red", type="CUE")

        assert cue.name == "Drop"
        assert cue.position == 60.5
        assert cue.color == "red"
        assert cue.type == "CUE"

    def test_conversion_config(self):
        """Test conversion configuration."""
        config = ConversionConfig(relative_paths=False, include_cue_points=False)

        assert config.relative_paths is False
        assert config.include_cue_points is False
        assert config.include_loops is True  # Default value


class TestUtils:
    """Test utility functions."""

    def test_normalize_path(self):
        """Test path normalization."""
        path = Path("/music/subfolder/song.mp3")
        base_path = Path("/music")

        # Test relative path
        result = normalize_path(path, base_path, use_relative=True)
        assert result == "subfolder/song.mp3"

        # Test absolute path
        result = normalize_path(path, base_path, use_relative=False)
        assert result == "/music/subfolder/song.mp3"

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename("Valid Name") == "Valid Name"
        assert sanitize_filename("Invalid<>Name") == "Invalid__Name"
        assert (
            sanitize_filename("Name:With|Special?Chars*") == "Name_With_Special_Chars_"
        )
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("   ") == "unnamed"


class TestConverter:
    """Test the main converter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConversionConfig()
        self.converter = RekordboxToTraktorConverter(self.config)

    @patch("universal_dj_usb.converter.create_rekordbox_parser")
    def test_convert_playlist_success(self, mock_parser_factory):
        """Test successful playlist conversion."""
        # Mock parser
        mock_parser = Mock()
        mock_playlist = Playlist(
            name="Test Playlist",
            tracks=[Track("Song 1", "Artist 1", Path("/music/song1.mp3"))],
        )
        mock_parser.get_playlist_by_name.return_value = mock_playlist
        mock_parser_factory.return_value = mock_parser

        # Mock NML generator
        with patch(
            "universal_dj_usb.converter.create_nml_generator"
        ) as mock_nml_factory:
            mock_nml = Mock()
            mock_nml.generate_nml.return_value = True
            mock_nml_factory.return_value = mock_nml

            # Test conversion
            with tempfile.TemporaryDirectory() as temp_dir:
                usb_path = Path(temp_dir) / "usb"
                output_path = Path(temp_dir) / "output.nml"

                result = self.converter.convert_playlist(
                    usb_path, "Test Playlist", output_path
                )

                assert result.success is True
                assert result.playlist_name == "Test Playlist"
                assert result.track_count == 1

    @patch("universal_dj_usb.converter.create_rekordbox_parser")
    def test_convert_playlist_not_found(self, mock_parser_factory):
        """Test conversion when playlist is not found."""
        # Mock parser
        mock_parser = Mock()
        mock_parser.get_playlist_by_name.return_value = None
        mock_parser_factory.return_value = mock_parser

        with tempfile.TemporaryDirectory() as temp_dir:
            usb_path = Path(temp_dir) / "usb"
            output_path = Path(temp_dir) / "output.nml"

            result = self.converter.convert_playlist(
                usb_path, "Nonexistent Playlist", output_path
            )

            assert result.success is False
            assert "not found" in result.error_message


class TestNMLGenerator:
    """Test the NML generator."""

    def test_track_entry_generation(self):
        """Test generating a track entry."""
        from universal_dj_usb.nml_generator import TraktorNMLGenerator

        config = ConversionConfig()
        generator = TraktorNMLGenerator(config)

        track = Track(
            title="Test Song",
            artist="Test Artist",
            file_path=Path("/music/test.mp3"),
            album="Test Album",
            bpm=128.0,
            duration=240.0,
        )

        entry = generator._create_track_entry(track)

        # Check that entry is properly structured
        assert entry.tag == "ENTRY"

        # Check for required sub-elements
        location = entry.find("LOCATION")
        assert location is not None
        assert location.get("FILE") == "test.mp3"

        artist_elem = entry.find("ARTIST")
        assert artist_elem is not None
        assert artist_elem.get("TITLE") == "Test Artist"

        title_elem = entry.find("TITLE")
        assert title_elem is not None
        assert title_elem.get("TITLE") == "Test Song"


class TestRekordboxParser:
    """Test the Rekordbox parser."""

    def test_parser_initialization(self):
        """Test parser initialization."""
        from universal_dj_usb.rekordbox_parser import RekordboxParser

        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            usb_path = Path(temp_dir)
            pioneer_path = usb_path / "PIONEER" / "rekordbox"
            pioneer_path.mkdir(parents=True)

            # Create mock export.pdb file
            export_file = pioneer_path / "export.pdb"
            export_file.write_bytes(b"mock pdb data" * 100)  # Make it big enough

            parser = RekordboxParser(usb_path)
            assert parser.usb_drive_path == usb_path
            assert parser.export_path == export_file

    def test_parser_invalid_export(self):
        """Test parser with invalid export."""
        from universal_dj_usb.rekordbox_parser import RekordboxParser

        with tempfile.TemporaryDirectory() as temp_dir:
            usb_path = Path(temp_dir)

            with pytest.raises(ValueError):
                RekordboxParser(usb_path)


if __name__ == "__main__":
    pytest.main([__file__])
