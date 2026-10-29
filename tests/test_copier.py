"""Tests for copying playlist audio files."""

from pathlib import Path

from universal_dj_usb.copier import CopyStatus, copy_playlist_files
from universal_dj_usb.models import Playlist, Track


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
    )


def test_copy_flat_filenames_into_playlist_folder(tmp_path):
    usb = _make_usb(tmp_path)
    tracks = [
        _track(usb, "Contents/Artist/Album/one.mp3", "One"),
        _track(usb, "Contents/Artist/Album/two.flac", "Two"),
    ]
    playlist = Playlist(name="Set A", tracks=tracks)
    output = tmp_path / "export"

    result = copy_playlist_files(playlist, usb, output)

    assert result.success
    assert result.destination_folder == output / "Set A"
    assert (
        output / "Set A" / "one.mp3"
    ).read_bytes() == b"audio:Contents/Artist/Album/one.mp3"
    assert (output / "Set A" / "two.flac").exists()
    assert result.copied_count == 2
    assert result.destinations_by_index[0] == output / "Set A" / "one.mp3"
    assert result.destinations_by_index[1] == output / "Set A" / "two.flac"


def test_numbered_files_follow_playlist_order(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(
        name="Ordered",
        tracks=[
            _track(usb, "Contents/z.mp3", "Z"),
            _track(usb, "Contents/a.mp3", "A"),
        ],
    )

    result = copy_playlist_files(playlist, usb, tmp_path / "export", number_files=True)

    assert (tmp_path / "export" / "Ordered" / "01 - z.mp3").exists()
    assert (tmp_path / "export" / "Ordered" / "02 - a.mp3").exists()
    assert result.destinations_by_index[0].name == "01 - z.mp3"
    assert result.destinations_by_index[1].name == "02 - a.mp3"


def test_existing_files_are_skipped_by_default(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(name="Set", tracks=[_track(usb, "Contents/song.mp3")])
    destination = tmp_path / "export" / "Set" / "song.mp3"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"old")

    result = copy_playlist_files(playlist, usb, tmp_path / "export")

    assert result.skipped_count == 1
    assert result.copied_count == 0
    assert destination.read_bytes() == b"old"
    assert result.destinations_by_index[0] == destination


def test_existing_files_can_be_overwritten(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(name="Set", tracks=[_track(usb, "Contents/song.mp3")])
    destination = tmp_path / "export" / "Set" / "song.mp3"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"old")

    result = copy_playlist_files(playlist, usb, tmp_path / "export", overwrite=True)

    assert result.copied_count == 1
    assert destination.read_bytes() == b"audio:Contents/song.mp3"


def test_duplicate_basenames_get_a_suffix(tmp_path):
    usb = _make_usb(tmp_path)
    first = _track(usb, "Contents/Artist/Album/song.mp3")
    second = _track(usb, "Contents/Other/Album/song.mp3")
    playlist = Playlist(name="Set", tracks=[first, second])

    result = copy_playlist_files(playlist, usb, tmp_path / "export")

    assert (tmp_path / "export" / "Set" / "song.mp3").exists()
    assert (tmp_path / "export" / "Set" / "song (2).mp3").exists()
    assert result.copied_count == 2


def test_duplicate_track_is_copied_once_without_numbers(tmp_path):
    usb = _make_usb(tmp_path)
    track = _track(usb, "Contents/song.mp3")
    playlist = Playlist(name="Set", tracks=[track, track])

    result = copy_playlist_files(playlist, usb, tmp_path / "export")

    assert (tmp_path / "export" / "Set" / "song.mp3").exists()
    assert result.copied_count == 1
    assert result.duplicate_count == 1
    assert result.destinations_by_index[0] == result.destinations_by_index[1]


def test_duplicate_track_gets_one_numbered_copy_per_position(tmp_path):
    usb = _make_usb(tmp_path)
    track = _track(usb, "Contents/song.mp3")
    playlist = Playlist(name="Set", tracks=[track, track])

    result = copy_playlist_files(playlist, usb, tmp_path / "export", number_files=True)

    assert (tmp_path / "export" / "Set" / "01 - song.mp3").exists()
    assert (tmp_path / "export" / "Set" / "02 - song.mp3").exists()
    assert result.copied_count == 2
    assert result.destinations_by_index[0] != result.destinations_by_index[1]


def test_missing_source_is_recorded_and_does_not_abort(tmp_path):
    usb = _make_usb(tmp_path)
    good = _track(usb, "Contents/good.mp3")
    missing = Track(
        title="Missing",
        artist="Artist",
        file_path=Path("/Contents/missing.mp3"),
    )
    playlist = Playlist(name="Set", tracks=[good, missing])

    result = copy_playlist_files(playlist, usb, tmp_path / "export")

    assert result.copied_count == 1
    assert result.missing_count == 1
    assert result.available_count == 1
    assert result.files[1].status == CopyStatus.MISSING
    assert 1 not in result.destinations_by_index


def test_playlist_folder_is_sanitized(tmp_path):
    usb = _make_usb(tmp_path)
    playlist = Playlist(name="A/B", tracks=[_track(usb, "Contents/song.mp3")])

    result = copy_playlist_files(playlist, usb, tmp_path / "export")

    assert result.destination_folder == tmp_path / "export" / "A_B"
    assert (tmp_path / "export" / "A_B" / "song.mp3").exists()
