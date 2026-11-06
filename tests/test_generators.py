"""Test the generator functionality."""

from pathlib import Path
from unittest.mock import Mock
from xml.etree import ElementTree as ET

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
    assert output_file.read_text(encoding="ascii").splitlines()[-1] == (
        track_path.as_posix()
    )


def test_m3u_output_inside_usb_root_uses_absolute_path_for_usb_track(tmp_path):
    """An output folder inside the USB root does not make USB tracks relative."""
    usb = tmp_path / "usb"
    track_path = usb / "Contents" / "song.mp3"
    track = Track(title="Track", artist="Artist", file_path=track_path)
    playlist = Playlist(name="Set", tracks=[track])
    output_file = usb / "exports" / "Set.m3u"

    result = M3UGenerator(ConversionConfig()).generate(playlist, output_file, usb)

    assert result.success
    assert output_file.read_text(encoding="ascii").splitlines()[-1] == (
        track_path.as_posix()
    )


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


def test_m3u8_absolute_paths_use_forward_slashes(tmp_path):
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


def test_m3u8_separate_format_folders_uses_shared_audio_relative_path(tmp_path):
    """Format folders may reference shared audio with parent-relative paths."""
    root = tmp_path / "export"
    track_file = root / "Set" / "song.mp3"
    track_file.parent.mkdir(parents=True)
    track_file.write_bytes(b"audio")
    track = Track(title="Track", artist="Artist", file_path=track_file)
    playlist = Playlist(name="Set", tracks=[track])
    output_file = root / "PLAYLISTS" / "M3U8" / "Set.m3u8"
    config = ConversionConfig(separate_format_folders=True)

    result = M3U8Generator(config).generate(playlist, output_file, root)

    assert result.success
    assert "../../Set/song.mp3" in output_file.read_text(encoding="utf-8")


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


def _nml_location_and_key(output_file: Path) -> tuple[dict, str]:
    """Return the first NML LOCATION attributes and PRIMARYKEY."""
    root = ET.fromstring(output_file.read_bytes())
    location = root.find("./COLLECTION/ENTRY/LOCATION")
    primarykey = root.find("./PLAYLISTS/NODE/SUBNODES/NODE/PLAYLIST/ENTRY/PRIMARYKEY")
    assert location is not None
    assert primarykey is not None
    return location.attrib, primarykey.attrib["KEY"]


def test_nml_normal_export_uses_usb_relative_location(tmp_path):
    """Normal NML export must use the USB as VOLUME and a volume-relative DIR."""
    usb = tmp_path / "usb"
    source = usb / "Contents" / "Artist" / "Album" / "song.mp3"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"audio")
    track = Track(
        title="Track",
        artist="Artist",
        file_path=Path("/Contents/Artist/Album/song.mp3"),
    )
    playlist = Playlist(name="Set", tracks=[track])
    output_file = tmp_path / "export" / "Set.nml"

    result = NMLGenerator(ConversionConfig()).generate(playlist, output_file, usb)

    location, key = _nml_location_and_key(output_file)
    volume = volume_name_for(usb)
    assert result.success
    assert location["VOLUME"] == volume
    assert location["DIR"] == "/:Contents/:Artist/:Album/:"
    assert location["FILE"] == "song.mp3"
    assert key == f"{volume}/:Contents/:Artist/:Album/:song.mp3"
    assert str(usb) not in location["DIR"]


def test_nml_export_to_usb_root_keeps_usb_relative_directory(tmp_path):
    """Writing the NML into the USB root must keep the known-good volume paths."""
    usb = tmp_path / "usb"
    source = usb / "Contents" / "Artist" / "Album" / "song.mp3"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"audio")
    track = Track(
        title="Track",
        artist="Artist",
        file_path=Path("/Contents/Artist/Album/song.mp3"),
    )
    playlist = Playlist(name="Set", tracks=[track])
    output_file = usb / "Set.nml"

    result = NMLGenerator(ConversionConfig()).generate(playlist, output_file, usb)

    location, key = _nml_location_and_key(output_file)
    volume = volume_name_for(usb)
    assert result.success
    assert location["VOLUME"] == volume
    assert location["DIR"] == "/:Contents/:Artist/:Album/:"
    assert key == f"{volume}/:Contents/:Artist/:Album/:song.mp3"


def test_nml_ignores_relative_paths_setting(tmp_path):
    """Traktor NML paths are always volume-relative, even in absolute mode."""
    output_dir = tmp_path / "export"
    copied = output_dir / "Set" / "song.mp3"
    copied.parent.mkdir(parents=True)
    copied.write_bytes(b"audio")
    track = Track(title="Track", artist="Artist", file_path=copied)
    playlist = Playlist(name="Set", tracks=[track])

    relative_file = output_dir / "relative.nml"
    absolute_file = output_dir / "absolute.nml"
    NMLGenerator(ConversionConfig(relative_paths=True)).generate(
        playlist, relative_file, output_dir
    )
    NMLGenerator(ConversionConfig(relative_paths=False)).generate(
        playlist, absolute_file, output_dir
    )

    relative_location, relative_key = _nml_location_and_key(relative_file)
    absolute_location, absolute_key = _nml_location_and_key(absolute_file)
    volume = volume_name_for(output_dir)
    assert relative_location["DIR"] == "/:Set/:"
    assert absolute_location["DIR"] == "/:Set/:"
    assert relative_location["VOLUME"] == volume
    assert absolute_location["VOLUME"] == volume
    assert relative_key == f"{volume}/:Set/:song.mp3"
    assert absolute_key == relative_key


def test_nml_uses_resolved_filename_for_windows_separator_path(tmp_path):
    """FILE and DIR must use the resolved USB path, not the raw PDB path."""
    usb = tmp_path / "usb"
    source = usb / "Contents" / "Artist" / "Album" / "song.mp3"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"audio")
    track = Track(
        title="Track",
        artist="Artist",
        file_path=Path(r"\Contents\Artist\Album\song.mp3"),
    )
    playlist = Playlist(name="Set", tracks=[track])
    output_file = tmp_path / "export" / "Set.nml"

    result = NMLGenerator(ConversionConfig()).generate(playlist, output_file, usb)

    location, key = _nml_location_and_key(output_file)
    volume = volume_name_for(usb)
    assert result.success
    assert location["FILE"] == "song.mp3"
    assert location["DIR"] == "/:Contents/:Artist/:Album/:"
    assert key == f"{volume}/:Contents/:Artist/:Album/:song.mp3"


def test_nml_preserves_unicode_filenames(tmp_path):
    """UTF-8 names with emoji and non-ASCII characters must survive NML output."""
    usb = tmp_path / "usb"
    filename = "01 - Café 🎵 (feat. 東京).mp3"
    source = usb / "Contents" / "Ärtist 🎧" / "Album ✨" / filename
    source.parent.mkdir(parents=True)
    source.write_bytes(b"audio")
    track = Track(title="Café 🎵 東京", artist="Ärtist 🎧", file_path=source)
    playlist = Playlist(name="Set ✨", tracks=[track])
    output_file = tmp_path / "export" / "Set.nml"

    result = NMLGenerator(ConversionConfig()).generate(playlist, output_file, usb)

    location, key = _nml_location_and_key(output_file)
    volume = volume_name_for(usb)
    assert result.success
    assert location["FILE"] == filename
    assert location["DIR"] == "/:Contents/:Ärtist 🎧/:Album ✨/:"
    assert key == f"{volume}/:Contents/:Ärtist 🎧/:Album ✨/:{filename}"


def test_nml_root_level_track_uses_root_directory(tmp_path):
    """A track directly in the volume root has an empty NML directory."""
    output_dir = tmp_path / "export"
    source = output_dir / "song.mp3"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"audio")
    track = Track(title="Track", artist="Artist", file_path=source)
    playlist = Playlist(name="Set", tracks=[track])
    output_file = output_dir / "Set.nml"

    result = NMLGenerator(ConversionConfig()).generate(
        playlist, output_file, output_dir
    )

    location, key = _nml_location_and_key(output_file)
    volume = volume_name_for(output_dir)
    assert result.success
    assert location["DIR"] == "/:"
    assert location["FILE"] == "song.mp3"
    assert key == f"{volume}/:song.mp3"


# Add more tests as needed...
