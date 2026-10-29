"""Tests for the shared playlist exporter."""

from pathlib import Path

from universal_dj_usb.exporter import export_playlists
from universal_dj_usb.models import ConversionConfig, Playlist, Track
from universal_dj_usb.paths import volume_name_for


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


def test_copy_and_nml_export_uses_export_root_as_volume(tmp_path):
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
    volume = volume_name_for(output)
    assert f'VOLUME="{volume}"' in text
    assert 'DIR="/:Set A/:"' in text
    assert 'FILE="song.mp3"' in text
    assert f"{volume}/:Set A/:song.mp3" in text


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
