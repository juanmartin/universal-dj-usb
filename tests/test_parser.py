"""Test the parser functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from universal_dj_usb.parser import RekordboxParser
from universal_dj_usb.models import Track, Playlist


def test_find_pdb_file():
    """Test PDB file detection."""
    usb_path = Path("test_usb")

    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True
        pdb_path = RekordboxParser.find_pdb_file(usb_path)

        expected = usb_path / "PIONEER" / "rekordbox" / "export.pdb"
        assert pdb_path == expected


def test_parser_initialization():
    """Test parser initialization."""
    pdb_path = Path("test.pdb")
    parser = RekordboxParser(pdb_path)

    assert parser.pdb_path == pdb_path
    assert parser.pdb_data is None
    assert parser._tracks_cache == {}
    assert parser._playlists_cache == []


# Add more tests as needed...
