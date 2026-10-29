"""CLI integration tests for the copy-file workflows."""

from pathlib import Path

from click.testing import CliRunner

from universal_dj_usb import cli as cli_module
from universal_dj_usb.cli import cli
from universal_dj_usb.models import Playlist, PlaylistTree, Track


class _FakeParser:
    """Minimal parser stand-in so CLI tests do not need a real PDB."""

    def __init__(self, playlist_tree: PlaylistTree):
        self.playlist_tree = playlist_tree

    def get_playlists(self, usb_path: Path) -> PlaylistTree:
        return self.playlist_tree

    def enhance_playlist_tracks(self, playlist: Playlist, usb_path: Path) -> Playlist:
        return playlist


def _make_playlist(tmp_path: Path) -> tuple:
    usb = tmp_path / "usb"
    source = usb / "Contents" / "Artist" / "Album" / "song.mp3"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"audio")
    track = Track(
        title="Song",
        artist="Artist",
        file_path=Path("/Contents/Artist/Album/song.mp3"),
        duration=180.0,
    )
    playlist = Playlist(name="Set", tracks=[track])
    tree = PlaylistTree(root_playlists=[playlist], all_playlists={1: playlist})
    return usb, playlist, tree


def _patch_parser(monkeypatch, tree: PlaylistTree) -> None:
    parser = _FakeParser(tree)
    monkeypatch.setattr(cli_module, "_open_database", lambda usb_path: parser)


def test_copy_files_command_copies_audio_only(monkeypatch, tmp_path):
    usb, _playlist, tree = _make_playlist(tmp_path)
    _patch_parser(monkeypatch, tree)
    output = tmp_path / "export"

    result = CliRunner().invoke(cli, ["copy-files", str(usb), str(output), "-p", "Set"])

    assert result.exit_code == 0, result.output
    assert (output / "Set" / "song.mp3").read_bytes() == b"audio"
    assert not (output / "Set.m3u8").exists()
    assert "1 copied" in result.output


def test_copy_files_command_deduplicates_repeated_selection(monkeypatch, tmp_path):
    usb, _playlist, tree = _make_playlist(tmp_path)
    _patch_parser(monkeypatch, tree)
    output = tmp_path / "export"

    result = CliRunner().invoke(
        cli,
        ["copy-files", str(usb), str(output), "-p", "Set", "-p", "Set"],
    )

    assert result.exit_code == 0, result.output
    assert (output / "Set" / "song.mp3").exists()
    assert not (output / "Set (2)").exists()


def test_convert_with_copy_files_numbers_tracks(monkeypatch, tmp_path):
    usb, _playlist, tree = _make_playlist(tmp_path)
    _patch_parser(monkeypatch, tree)
    output = tmp_path / "export"

    result = CliRunner().invoke(
        cli,
        [
            "convert",
            str(usb),
            "-p",
            "Set",
            "-o",
            str(output),
            "-f",
            "m3u8",
            "--copy-files",
            "--number-files",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output / "Set" / "01 - song.mp3").exists()
    text = (output / "Set.m3u8").read_text(encoding="utf-8")
    assert "Set/01 - song.mp3" in text


def test_copy_flags_without_copy_files_are_rejected(monkeypatch, tmp_path):
    usb, _playlist, tree = _make_playlist(tmp_path)
    _patch_parser(monkeypatch, tree)
    output = tmp_path / "export"

    result = CliRunner().invoke(
        cli,
        [
            "convert",
            str(usb),
            "-o",
            str(output),
            "--number-files",
        ],
    )

    assert result.exit_code == 2
    assert "--number-files requires --copy-files" in result.output
