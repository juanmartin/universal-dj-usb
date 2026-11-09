"""Tests for the shared playlist exporter."""

import platform
from pathlib import Path

import pytest

from universal_dj_usb.exporter import export_playlists
from universal_dj_usb.models import ConversionConfig, Playlist, Track
from universal_dj_usb.paths import nml_volume_root_for, volume_name_for


def _make_usb(tmp_path: Path) -> Path:
    usb = tmp_path / "usb"
    (usb / "Contents").mkdir(parents=True)
    return usb


def _track(usb: Path, relative: str, title: str = "Track") -> Track:
    source = usb / relative
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(f"audio:{relative}".encode())
    return Track(
        title=title,
        artist="Artist",
        file_path=Path("/" + relative.replace("\\", "/")),
        duration=180.0,
    )


def test_copy_and_m3u8_export_is_self_contained(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(
        name="Set A",
        tracks=[_track(usb, "Contents/Artist/Album/song.mp3")],
    )
    output = tmp_path / "export"
    config = ConversionConfig(output_format="m3u8", copy_files=True)

    result = export_playlists([playlist], usb, output, config)

    playlist_file = output / "Set A.m3u8"
    copied_file = output / "Set A" / "song.mp3"
    assert result.success
    assert playlist_file.exists()
    assert copied_file.exists()
    assert "Set A/song.mp3" in playlist_file.read_text(encoding="utf-8")
    assert str(usb) not in playlist_file.read_text(encoding="utf-8")


def test_copy_and_nml_export_uses_the_volume_root(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(
        name="Set A",
        tracks=[_track(usb, "Contents/Artist/Album/song.mp3")],
    )
    output = tmp_path / "export"
    config = ConversionConfig(output_format="nml", copy_files=True)

    result = export_playlists([playlist], usb, output, config)

    playlist_file = output / "Set A.nml"
    text = playlist_file.read_text(encoding="utf-8")
    assert result.success
    assert playlist_file.exists()

    volume_root = nml_volume_root_for(output)
    volume = volume_name_for(volume_root)
    if platform.system() == "Windows":
        relative_output = "/".join(output.relative_to(volume_root).parts)
        dir_prefix = f"/:{relative_output.replace('/', '/:')}/:"
        key_prefix = f"{volume}/:{relative_output.replace('/', '/:')}/:"
    else:
        dir_prefix = "/:"
        key_prefix = f"{volume}/:"

    assert f'VOLUME="{volume}"' in text
    assert f'DIR="{dir_prefix}Set A/:"' in text
    assert 'FILE="song.mp3"' in text
    assert f"{key_prefix}Set A/:song.mp3" in text


@pytest.mark.skipif(
    platform.system() != "Windows",
    reason="Windows drive-root NML semantics",
)
def test_copy_and_nml_export_on_windows_keeps_output_folder_in_path(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(
        name="HONGUI GURL",
        tracks=[_track(usb, "Contents/Artist/Album/song.mp3")],
    )
    output = tmp_path / "udj-new-PLAYLISTS" / "windows"
    config = ConversionConfig(output_format="nml", copy_files=True)

    export_playlists([playlist], usb, output, config)

    text = (output / "HONGUI GURL.nml").read_text(encoding="utf-8")
    drive_root = Path(output.anchor)
    volume = volume_name_for(drive_root)
    relative_output = "/".join(output.relative_to(drive_root).parts)
    expected_dir = f"/:{relative_output.replace('/', '/:')}/:HONGUI GURL/:"
    expected_key = (
        f"{volume}/:{relative_output.replace('/', '/:')}/:HONGUI GURL/:song.mp3"
    )

    assert f'VOLUME="{volume}"' in text
    assert f'DIR="{expected_dir}"' in text
    assert f'PRIMARYKEY TYPE="TRACK" KEY="{expected_key}"' in text


def test_numbered_copy_is_reflected_in_playlist(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(
        name="Ordered",
        tracks=[
            _track(usb, "Contents/z.mp3", "Z"),
            _track(usb, "Contents/a.mp3", "A"),
        ],
    )
    output = tmp_path / "export"
    config = ConversionConfig(output_format="m3u8", copy_files=True, number_files=True)

    export_playlists([playlist], usb, output, config)
    text = (output / "Ordered.m3u8").read_text(encoding="utf-8")

    assert "Ordered/01 - z.mp3" in text
    assert "Ordered/02 - a.mp3" in text


def test_missing_tracks_are_excluded_from_playlist(tmp_path):
    usb = _make_usb(tmp_path)
    good = _track(usb, "Contents/good.mp3")
    missing = Track(
        title="Missing",
        artist="Artist",
        file_path=Path("/Contents/missing.mp3"),
        duration=120.0,
    )
    playlist = Playlist(name="Set", tracks=[good, missing])
    output = tmp_path / "export"
    config = ConversionConfig(output_format="m3u8", copy_files=True)

    result = export_playlists([playlist], usb, output, config)
    text = (output / "Set.m3u8").read_text(encoding="utf-8")

    assert "Set/good.mp3" in text
    assert "Set/missing.mp3" not in text
    assert result.total_missing == 1
    assert result.conversions[0].track_count == 1
    assert any(
        "could not be copied" in warning for warning in result.conversions[0].warnings
    )


def test_copy_only_produces_no_playlist_files(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(name="Set", tracks=[_track(usb, "Contents/song.mp3")])
    output = tmp_path / "export"
    config = ConversionConfig(output_format="m3u8", copy_files=True)

    result = export_playlists([playlist], usb, output, config, generate_playlists=False)

    assert result.conversions == []
    assert result.total_copied == 1
    assert (output / "Set" / "song.mp3").exists()
    assert not (output / "Set.m3u8").exists()


def test_no_copy_export_keeps_original_track_paths(tmp_path):
    usb = _make_usb(tmp_path)
    source = usb / "Contents" / "Artist" / "Album" / "song.mp3"
    playlist = Playlist(
        name="Set", tracks=[_track(usb, "Contents/Artist/Album/song.mp3")]
    )
    output = tmp_path / "export"
    config = ConversionConfig(output_format="m3u8")

    result = export_playlists([playlist], usb, output, config)
    text = (output / "Set.m3u8").read_text(encoding="utf-8")

    assert result.success
    assert result.copies == []
    assert source.as_posix() in text
    assert not (output / "Set").exists()


def test_no_copy_nml_export_uses_usb_relative_location(tmp_path):
    """Normal NML export must not put the absolute USB path in LOCATION/DIR."""
    usb = _make_usb(tmp_path)
    playlist = Playlist(
        name="Set", tracks=[_track(usb, "Contents/Artist/Album/song.mp3")]
    )
    output = tmp_path / "export"
    config = ConversionConfig(output_format="nml")

    result = export_playlists([playlist], usb, output, config)
    text = (output / "Set.nml").read_text(encoding="utf-8")
    volume = volume_name_for(usb)

    assert result.success
    assert f'VOLUME="{volume}"' in text
    assert 'DIR="/:Contents/:Artist/:Album/:"' in text
    assert 'FILE="song.mp3"' in text
    assert f"{volume}/:Contents/:Artist/:Album/:song.mp3" in text
    assert str(usb) not in text


def test_convert_and_copy_writes_all_requested_formats(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(name="Set", tracks=[_track(usb, "Contents/song.mp3")])
    output = tmp_path / "export"
    config = ConversionConfig(output_format="all", copy_files=True)

    result = export_playlists([playlist], usb, output, config)

    assert (output / "Set.nml").exists()
    assert (output / "Set.m3u").exists()
    assert (output / "Set.m3u8").exists()
    assert result.total_copied == 1
    assert len(result.conversions) == 3


def test_separate_format_folders_share_audio(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(
        name="Set", tracks=[_track(usb, "Contents/Artist/Album/song.mp3")]
    )
    output = tmp_path / "export"
    config = ConversionConfig(
        output_format="all",
        copy_files=True,
        separate_format_folders=True,
    )

    result = export_playlists([playlist], usb, output, config)

    assert (output / "PLAYLISTS" / "NML" / "Set.nml").exists()
    assert (output / "PLAYLISTS" / "M3U" / "Set.m3u").exists()
    assert (output / "PLAYLISTS" / "M3U8" / "Set.m3u8").exists()
    assert (output / "Set" / "song.mp3").exists()
    assert not (output / "PLAYLISTS" / "Set").exists()
    assert result.total_copied == 1

    m3u8_text = (output / "PLAYLISTS" / "M3U8" / "Set.m3u8").read_text(encoding="utf-8")
    m3u_text = (output / "PLAYLISTS" / "M3U" / "Set.m3u").read_text(encoding="ascii")
    assert "../../Set/song.mp3" in m3u8_text
    assert "../../Set/song.mp3" in m3u_text


def test_separate_format_folders_without_copy(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(
        name="Set", tracks=[_track(usb, "Contents/Artist/Album/song.mp3")]
    )
    output = tmp_path / "export"
    config = ConversionConfig(
        output_format="all",
        separate_format_folders=True,
    )

    result = export_playlists([playlist], usb, output, config)

    assert result.success
    assert (output / "PLAYLISTS" / "NML" / "Set.nml").exists()
    assert (output / "PLAYLISTS" / "M3U" / "Set.m3u").exists()
    assert (output / "PLAYLISTS" / "M3U8" / "Set.m3u8").exists()
    assert not (output / "Set").exists()


def test_playlist_named_playlists_does_not_collide_with_format_parent(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(
        name="PLAYLISTS", tracks=[_track(usb, "Contents/Artist/Album/song.mp3")]
    )
    output = tmp_path / "export"
    config = ConversionConfig(
        output_format="m3u8",
        copy_files=True,
        separate_format_folders=True,
    )

    result = export_playlists([playlist], usb, output, config)

    assert result.success
    assert (output / "PLAYLISTS (2)" / "song.mp3").exists()
    assert (output / "PLAYLISTS" / "M3U8" / "PLAYLISTS (2).m3u8").exists()


def test_export_can_be_cancelled_before_it_starts(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(name="Set", tracks=[_track(usb, "Contents/song.mp3")])
    output = tmp_path / "export"
    config = ConversionConfig(output_format="m3u8", copy_files=True)

    result = export_playlists(
        [playlist],
        usb,
        output,
        config,
        is_cancelled=lambda: True,
    )

    assert result.cancelled
    assert not result.success
    assert not (output / "Set.m3u8").exists()
    assert not (output / "Set").exists()


def test_duplicate_playlist_names_get_separate_folders(tmp_path):
    usb = _make_usb(tmp_path)
    first = Playlist(name="Set", tracks=[_track(usb, "Contents/one.mp3")])
    second = Playlist(name="Set", tracks=[_track(usb, "Contents/two.mp3")])
    output = tmp_path / "export"
    config = ConversionConfig(output_format="m3u8", copy_files=True)

    result = export_playlists([first, second], usb, output, config)

    assert (output / "Set" / "one.mp3").exists()
    assert (output / "Set (2)" / "two.mp3").exists()
    assert (output / "Set.m3u8").exists()
    assert (output / "Set (2).m3u8").exists()
    assert result.total_copied == 2


def test_relative_output_directory_is_resolved(tmp_path, monkeypatch):
    usb = _make_usb(tmp_path)
    playlist = Playlist(name="Set", tracks=[_track(usb, "Contents/song.mp3")])
    monkeypatch.chdir(tmp_path)
    config = ConversionConfig(output_format="m3u8", copy_files=True)

    result = export_playlists([playlist], usb, Path("export"), config)

    assert (tmp_path / "export" / "Set" / "song.mp3").exists()
    assert (tmp_path / "export" / "Set.m3u8").exists()
    text = (tmp_path / "export" / "Set.m3u8").read_text(encoding="utf-8")
    assert "Set/song.mp3" in text
    assert result.total_copied == 1
