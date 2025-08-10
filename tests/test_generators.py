"""Test the generator functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from universal_dj_usb.models import Track, Playlist, ConversionConfig
from universal_dj_usb.generators import M3UGenerator, M3U8Generator, NMLGenerator


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return ConversionConfig(relative_paths=True)


@pytest.fixture
def sample_track():
    """Sample track for testing."""
    return Track(
        title="Test Song",
        artist="Test Artist",
        file_path=Path("Music/test.mp3"),
        album="Test Album",
        duration=180.0,
        bpm=120.0,
    )


@pytest.fixture
def sample_playlist(sample_track):
    """Sample playlist for testing."""
    playlist = Playlist(name="Test Playlist", tracks=[sample_track])
    return playlist


def test_m3u_generator(sample_config, sample_playlist):
    """Test M3U generator."""
    generator = M3UGenerator(sample_config)
    assert generator.file_extension == ".m3u"


def test_m3u8_generator(sample_config, sample_playlist):
    """Test M3U8 generator."""
    generator = M3U8Generator(sample_config)
    assert generator.file_extension == ".m3u8"


def test_nml_generator(sample_config, sample_playlist):
    """Test NML generator."""
    generator = NMLGenerator(sample_config)
    assert generator.file_extension == ".nml"


# Add more tests as needed...
