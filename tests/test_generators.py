"""Test the generator functionality."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from universal_dj_usb.generators import M3U8Generator, M3UGenerator, NMLGenerator
from universal_dj_usb.models import ConversionConfig, Playlist, Track
from universal_dj_usb.paths import volume_name_for


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


def test_m3u_relative_path_when_track_is_inside_output_dir(tmp_path):
    """A copied track inside the output directory gets a portable relative path."""
    output_dir = tmp_path / "export"
    track = Track(
        title="Track",
        artist="Artist",
        file_path=output_dir / "Set" / "song.mp3",
        duration=180.0,
    )
    playlist = Playlist(name="Set", tracks=[track])
    output_file = output_dir / "Set.m3u"

    result = M3UGenerator(ConversionConfig()).generate(
        playlist, output_file, output_dir
    )

    assert result.success
    assert "Set/song.mp3" in output_file.read_text(encoding="ascii")


def test_m3u_keeps_absolute_path_when_track_is_outside_output_dir(tmp_path):
    """A track outside the output directory is not turned into a fragile ../ path."""
    track_path = tmp_path / "usb" / "Contents" / "song.mp3"
    track = Track(title="Track", artist="Artist", file_path=track_path)
    playlist = Playlist(name="Set", tracks=[track])
    output_file = tmp_path / "export" / "Set.m3u"

    result = M3UGenerator(ConversionConfig()).generate(
        playlist, output_file, tmp_path / "usb"
    )

    assert result.success
    assert track_path.as_posix() in output_file.read_text(encoding="ascii")


def test_m3u_output_inside_usb_root_uses_absolute_path_for_usb_track(tmp_path):
    """An output folder inside the USB root does not make USB tracks relative."""
    usb = tmp_path / "usb"
    track_path = usb / "Contents" / "song.mp3"
    track = Track(title="Track", artist="Artist", file_path=track_path)
    playlist = Playlist(name="Set", tracks=[track])
    output_file = usb / "exports" / "Set.m3u"

    result = M3UGenerator(ConversionConfig()).generate(playlist, output_file, usb)

    assert result.success
    assert track_path.as_posix() in output_file.read_text(encoding="ascii")


def test_m3u_absolute_paths_work_with_copied_destination_paths(tmp_path):
    """Absolute mode must not re-anchor an already absolute copied path at the USB root."""
    output_dir = tmp_path / "export"
    copied = output_dir / "Set" / "song.mp3"
    track = Track(title="Track", artist="Artist", file_path=copied)
    playlist = Playlist(name="Set", tracks=[track])
    output_file = output_dir / "Set.m3u"
    config = ConversionConfig(m3u_absolute_paths=True)

    result = M3UGenerator(config).generate(playlist, output_file, output_dir)

    assert result.success
    assert copied.as_posix() in output_file.read_text(encoding="ascii")


def test_m3u_absolute_paths_use_forward_slashes(tmp_path):
    """Absolute entries still use playlist-safe forward slashes."""
    windows_style = Path(r"C:\Music\song.mp3")
    track = Track(title="Track", artist="Artist", file_path=windows_style)
    playlist = Playlist(name="Set", tracks=[track])
    output_file = tmp_path / "Set.m3u"
    config = ConversionConfig(m3u_absolute_paths=True)

    result = M3UGenerator(config).generate(playlist, output_file, None)

    assert result.success
    text = output_file.read_text(encoding="ascii")
    assert "C:/Music/song.mp3" in text
    assert "\\" not in text


def test_nml_relative_location_and_key_for_copied_track(tmp_path):
    """NML uses the output root as the pseudo-volume for copied exports."""
    output_dir = tmp_path / "export"
    copied = output_dir / "Set" / "song.mp3"
    track = Track(title="Track", artist="Artist", file_path=copied)
    playlist = Playlist(name="Set", tracks=[track])
    output_file = output_dir / "Set.nml"

    result = NMLGenerator(ConversionConfig()).generate(
        playlist, output_file, output_dir
    )

    text = output_file.read_text(encoding="utf-8")
    assert result.success
    volume = volume_name_for(output_dir)
    assert f'VOLUME="{volume}"' in text
    assert 'DIR="/:Set/:"' in text
    assert 'FILE="song.mp3"' in text
    assert f"{volume}/:Set/:song.mp3" in text


# Add more tests as needed...
