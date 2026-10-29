"""Tests for shared path helpers."""

from pathlib import Path

from universal_dj_usb.paths import (
    relative_path_if_inside,
    resolve_track_source,
    sanitize_filename,
    unique_name,
)


def test_sanitize_filename_replaces_invalid_characters():
    assert sanitize_filename('A/B:C*D?"E<F>G|H\\I') == "A_B_C_D__E_F_G_H_I"


def test_sanitize_filename_falls_back_to_playlist():
    assert sanitize_filename("  ...  ") == "playlist"


def test_unique_name_adds_numeric_suffix_case_insensitively():
    used = {"song.mp3", "song (2).mp3"}
    assert unique_name("Song.MP3", used) == "Song (3).MP3"


def test_resolve_track_source_contents_variants(tmp_path):
    usb = tmp_path / "usb"
    source = usb / "Contents" / "Artist" / "Album" / "song.mp3"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"audio")

    variants = [
        Path("/Contents/Artist/Album/song.mp3"),
        Path("Contents/Artist/Album/song.mp3"),
        Path("C:/Users/other/Music/Contents/Artist/Album/song.mp3"),
        Path("\\Contents\\Artist\\Album\\song.mp3"),
    ]

    for variant in variants:
        assert resolve_track_source(variant, usb) == source


def test_resolve_track_source_prefers_existing_absolute_path(tmp_path):
    absolute = tmp_path / "local" / "song.mp3"
    absolute.parent.mkdir()
    absolute.write_bytes(b"audio")

    usb = tmp_path / "usb"
    usb.mkdir()

    assert resolve_track_source(absolute, usb) == absolute


def test_resolve_track_source_falls_back_to_usb_join(tmp_path):
    usb = tmp_path / "usb"
    source = usb / "Music" / "song.mp3"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"audio")

    assert resolve_track_source(Path("/Music/song.mp3"), usb) == source


def test_relative_path_if_inside(tmp_path):
    base = tmp_path / "export"
    inside = base / "Set A" / "song.mp3"
    outside = tmp_path / "usb" / "song.mp3"

    assert relative_path_if_inside(inside, base) == "Set A/song.mp3"
    assert relative_path_if_inside(outside, base) is None
