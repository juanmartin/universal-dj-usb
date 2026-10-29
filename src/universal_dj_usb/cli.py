"""Command-line interface for the Universal DJ USB playlist converter."""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import click
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from . import __version__
from .exporter import ExportResult, export_playlists
from .models import ConversionConfig, Playlist, PlaylistTree
from .parser import RekordboxParser

console = Console()
logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False) -> None:
    """Set up logging configuration."""
    if debug:
        # Debug mode: show all logs
        log_level = logging.DEBUG
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    else:
        # Normal mode: only show warnings and errors, suppress INFO from parser
        logging.basicConfig(
            level=logging.WARNING,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        # Set parser to WARNING level to hide INFO messages
        parser_logger = logging.getLogger("universal_dj_usb.parser")
        parser_logger.setLevel(logging.WARNING)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.version_option(
    version=__version__, prog_name="Universal DJ USB Playlist Converter"
)
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """Universal DJ USB Playlist Converter.

    Convert Rekordbox USB playlists to various formats (NML, M3U, M3U8).
    """
    setup_logging(debug)
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug


@cli.command()
@click.argument("usb_path", type=click.Path(exists=True, path_type=Path))
def detect(usb_path: Path) -> None:
    """Detect and validate Rekordbox data on USB drive."""
    console.print(f"[bold blue]Checking USB drive:[/bold blue] {usb_path}")

    pdb_path = RekordboxParser.find_pdb_file(usb_path)
    if pdb_path:
        console.print(f"[green]✓ Found Rekordbox database:[/green] {pdb_path}")

        # Try to parse and show basic info
        parser = RekordboxParser(pdb_path)
        if parser.parse():
            playlist_tree = parser.get_playlists(usb_path)
            console.print("[green]✓ Successfully parsed database[/green]")
            console.print(f"Found {len(playlist_tree.all_playlists)} playlists")
        else:
            console.print("[red]✗ Failed to parse database[/red]")
    else:
        console.print("[red]✗ No Rekordbox database found[/red]")


@cli.command()
@click.argument("usb_path", type=click.Path(exists=True, path_type=Path))
def list_playlists(usb_path: Path) -> None:
    """List all available playlists on the USB drive."""
    console.print(f"[bold blue]Listing playlists from:[/bold blue] {usb_path}")

    pdb_path = RekordboxParser.find_pdb_file(usb_path)
    if not pdb_path:
        console.print("[red]✗ No Rekordbox database found[/red]")
        return

    parser = RekordboxParser(pdb_path)
    if not parser.parse():
        console.print("[red]✗ Failed to parse database[/red]")
        return

    playlist_tree = parser.get_playlists(usb_path)

    if not playlist_tree.all_playlists:
        console.print("[yellow]No playlists found[/yellow]")
        return

    # Create table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=6)
    table.add_column("Name", style="cyan")
    table.add_column("Tracks", justify="right", style="green")
    table.add_column("Type", style="blue")

    for playlist in playlist_tree.all_playlists.values():
        playlist_type = "Folder" if playlist.is_folder else "Playlist"
        table.add_row(
            str(playlist.id or ""),
            playlist.name,
            str(playlist.track_count),
            playlist_type,
        )

    console.print(table)


def _open_database(usb_path: Path) -> Optional[RekordboxParser]:
    """Find and parse the Rekordbox database, printing errors."""
    pdb_path = RekordboxParser.find_pdb_file(usb_path)
    if not pdb_path:
        console.print("[red]✗ No Rekordbox database found[/red]")
        return None

    parser = RekordboxParser(pdb_path)
    if not parser.parse():
        console.print("[red]✗ Failed to parse database[/red]")
        return None
    return parser


def _select_playlists(
    playlist_tree: PlaylistTree, names: Tuple[str, ...]
) -> List[Playlist]:
    """Select named playlists, or every non-empty playlist when no names are given."""
    selected: List[Playlist] = []
    seen: set[int] = set()
    if names:
        for name in names:
            found = playlist_tree.get_playlist_by_name(name)
            if found and id(found) not in seen:
                seen.add(id(found))
                selected.append(found)
            elif not found:
                console.print(f"[yellow]Warning: Playlist '{name}' not found[/yellow]")
    else:
        selected = [
            playlist
            for playlist in playlist_tree.all_playlists.values()
            if not playlist.is_folder and playlist.track_count > 0
        ]
    return selected


def _print_copy_summary(export_result: ExportResult) -> None:
    """Print per-playlist copy counts and an aggregate summary."""
    for copy_result in export_result.copies:
        console.print(
            f"[cyan]📁 {copy_result.playlist_name}[/cyan]: "
            f"{copy_result.copied_count} copied, "
            f"{copy_result.skipped_count} skipped, "
            f"{copy_result.duplicate_count} duplicates, "
            f"{copy_result.missing_count} missing, "
            f"{copy_result.error_count} errors → {copy_result.destination_folder}"
        )
        if copy_result.error:
            console.print(f"  [red]✗[/red] {copy_result.error}")
        for item in copy_result.files:
            if item.status.value in ("missing", "error") and item.error:
                console.print(f"  [yellow]⚠[/yellow] {item.error}")

    console.print(
        f"[bold]Files:[/bold] {export_result.total_copied} copied, "
        f"{export_result.total_skipped} skipped, "
        f"{export_result.total_duplicates} duplicates, "
        f"{export_result.total_missing} missing, "
        f"{export_result.total_errors} errors"
    )


@cli.command()
@click.argument("usb_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory for playlist files",
)
@click.option(
    "--playlist",
    "-p",
    multiple=True,
    help="Specific playlist names to convert (can be used multiple times)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["nml", "m3u", "m3u8", "all"], case_sensitive=False),
    default="nml",
    help="Output format",
)
@click.option(
    "--relative-paths/--absolute-paths",
    default=True,
    help="Use relative or absolute file paths",
)
@click.option(
    "--use-format-suffix",
    is_flag=True,
    default=False,
    help="Append format suffix to filenames (e.g., -NML.nml for Traktor compatibility)",
)
@click.option(
    "--m3u-extended/--m3u-simple",
    default=True,
    help=(
        "Use extended M3U format with metadata (default) or simple format "
        "(paths only)"
    ),
)
@click.option(
    "--m3u-absolute-paths/--m3u-relative-paths",
    default=False,
    help="Use absolute paths in M3U files instead of relative paths",
)
@click.option(
    "--copy-files",
    is_flag=True,
    default=False,
    help="Copy each playlist's audio into a per-playlist folder",
)
@click.option(
    "--number-files",
    is_flag=True,
    default=False,
    help="Prefix copied filenames with their playlist position (requires --copy-files)",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing copied files instead of skipping them",
)
@click.pass_context
def convert(
    ctx: click.Context,
    usb_path: Path,
    output: Optional[Path],
    playlist: Tuple[str, ...],
    format: str,
    relative_paths: bool,
    use_format_suffix: bool,
    m3u_extended: bool,
    m3u_absolute_paths: bool,
    copy_files: bool,
    number_files: bool,
    overwrite: bool,
) -> None:
    """Convert Rekordbox playlists to specified format(s)."""
    debug = ctx.obj.get("debug", False)

    if number_files and not copy_files:
        raise click.UsageError("--number-files requires --copy-files")
    if overwrite and not copy_files:
        raise click.UsageError("--overwrite requires --copy-files")

    # Set default output path
    if output is None:
        output = Path.cwd() / "converted_playlists"

    console.print(f"[bold blue]Converting playlists from:[/bold blue] {usb_path}")
    console.print(f"[bold blue]Output directory:[/bold blue] {output}")
    console.print(f"[bold blue]Format:[/bold blue] {format}")
    if copy_files:
        console.print("[bold blue]Copy audio files:[/bold blue] yes")

    parser = _open_database(usb_path)
    if parser is None:
        return

    playlist_tree = parser.get_playlists(usb_path)
    if not playlist_tree.all_playlists:
        console.print("[yellow]No playlists found[/yellow]")
        return

    playlists_to_convert = _select_playlists(playlist_tree, playlist)
    if not playlists_to_convert:
        console.print("[yellow]No playlists to convert[/yellow]")
        return

    config = ConversionConfig(
        relative_paths=relative_paths,
        output_format=format.lower(),
        use_format_suffix=use_format_suffix,
        m3u_extended=m3u_extended,
        m3u_absolute_paths=m3u_absolute_paths,
        copy_files=copy_files,
        number_files=number_files,
        overwrite_files=overwrite,
    )

    with Progress() as progress:
        task = progress.add_task("Exporting playlists...", total=100)

        def on_progress(message: str, percent: int) -> None:
            progress.update(task, completed=percent, description=message)

        export_result = export_playlists(
            playlists=playlists_to_convert,
            usb_path=usb_path,
            output_dir=output,
            config=config,
            parser=parser,
            enhance=True,
            generate_playlists=True,
            progress_callback=on_progress,
        )

    for conversion in export_result.conversions:
        output_name = (
            conversion.output_file.name if conversion.output_file else "(unknown)"
        )
        if conversion.success:
            console.print(
                f"[green]✓[/green] {conversion.playlist_name} → {output_name}"
            )
            if debug and conversion.warnings:
                for warning in conversion.warnings:
                    console.print(f"  [yellow]⚠[/yellow] {warning}")
        else:
            console.print(
                f"[red]✗[/red] {conversion.playlist_name}: {conversion.error_message}"
            )

    successful = len(export_result.successful_conversions)
    total = len(export_result.conversions)
    failed = total - successful

    console.print()
    if total and successful == total:
        file_word = "playlist file" if successful == 1 else "playlist files"
        console.print(
            f"[bold green]✅ Successfully converted {successful} "
            f"{file_word}[/bold green]"
        )
    elif total:
        console.print(
            f"[yellow]⚠ Converted {successful}/{total} playlist files "
            f"({failed} failed)[/yellow]"
        )

    for conversion in export_result.successful_conversions:
        output_name = (
            conversion.output_file.name if conversion.output_file else "(unknown)"
        )
        console.print(
            f"[cyan]📁 {conversion.playlist_name}[/cyan]: "
            f"{conversion.track_count} tracks → {output_name}"
        )

    if copy_files:
        _print_copy_summary(export_result)

    console.print(f"[dim]Output directory: {output}[/dim]")

    # Debug info
    if debug:
        console.print("\n[dim]Debug Info:[/dim]")
        console.print(f"[dim]• Input path: {usb_path}[/dim]")
        console.print(f"[dim]• Format: {format}[/dim]")
        console.print(f"[dim]• Relative paths: {relative_paths}[/dim]")
        console.print(f"[dim]• Use format suffix: {use_format_suffix}[/dim]")
        console.print(f"[dim]• Copy files: {copy_files}[/dim]")
        console.print(f"[dim]• Number files: {number_files}[/dim]")
        console.print(f"[dim]• Overwrite files: {overwrite}[/dim]")
        if format.lower() in ["m3u", "m3u8", "all"]:
            console.print(f"[dim]• M3U extended format: {m3u_extended}[/dim]")
            console.print(f"[dim]• M3U absolute paths: {m3u_absolute_paths}[/dim]")
        if any(r.warnings for r in export_result.conversions):
            warning_count = sum(len(r.warnings) for r in export_result.conversions)
            console.print(f"[dim]• Total warnings: {warning_count}[/dim]")


@cli.command("copy-files")
@click.argument("usb_path", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
@click.option(
    "--playlist",
    "-p",
    multiple=True,
    help="Specific playlist names to copy (can be used multiple times)",
)
@click.option(
    "--number-files",
    is_flag=True,
    default=False,
    help="Prefix copied filenames with their playlist position",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing files instead of skipping them",
)
@click.pass_context
def copy_files(
    ctx: click.Context,
    usb_path: Path,
    output: Path,
    playlist: Tuple[str, ...],
    number_files: bool,
    overwrite: bool,
) -> None:
    """Copy the audio files of playlists into per-playlist folders."""
    debug = ctx.obj.get("debug", False)

    console.print(f"[bold blue]Copying playlist files from:[/bold blue] {usb_path}")
    console.print(f"[bold blue]Destination:[/bold blue] {output}")

    parser = _open_database(usb_path)
    if parser is None:
        return

    playlist_tree = parser.get_playlists(usb_path)
    if not playlist_tree.all_playlists:
        console.print("[yellow]No playlists found[/yellow]")
        return

    playlists_to_copy = _select_playlists(playlist_tree, playlist)
    if not playlists_to_copy:
        console.print("[yellow]No playlists to copy[/yellow]")
        return

    config = ConversionConfig(
        copy_files=True,
        number_files=number_files,
        overwrite_files=overwrite,
    )

    with Progress() as progress:
        task = progress.add_task("Copying playlist files...", total=100)

        def on_progress(message: str, percent: int) -> None:
            progress.update(task, completed=percent, description=message)

        export_result = export_playlists(
            playlists=playlists_to_copy,
            usb_path=usb_path,
            output_dir=output,
            config=config,
            parser=None,
            enhance=False,
            generate_playlists=False,
            progress_callback=on_progress,
        )

    _print_copy_summary(export_result)
    console.print(f"[dim]Destination: {output}[/dim]")

    if debug:
        console.print("\n[dim]Debug Info:[/dim]")
        console.print(f"[dim]• Input path: {usb_path}[/dim]")
        console.print(f"[dim]• Number files: {number_files}[/dim]")
        console.print(f"[dim]• Overwrite files: {overwrite}[/dim]")


@cli.command()
@click.argument("usb_path", type=click.Path(exists=True, path_type=Path))
@click.argument("playlist_name")
def info(usb_path: Path, playlist_name: str) -> None:
    """Get detailed information about a specific playlist."""
    console.print(f"[bold blue]Getting info for playlist:[/bold blue] {playlist_name}")

    pdb_path = RekordboxParser.find_pdb_file(usb_path)
    if not pdb_path:
        console.print("[red]✗ No Rekordbox database found[/red]")
        return

    parser = RekordboxParser(pdb_path)
    if not parser.parse():
        console.print("[red]✗ Failed to parse database[/red]")
        return

    playlist_tree = parser.get_playlists(usb_path)
    playlist = playlist_tree.get_playlist_by_name(playlist_name)

    if not playlist:
        console.print(f"[red]✗ Playlist '{playlist_name}' not found[/red]")
        return

    # Display playlist info
    console.print(f"[bold cyan]Name:[/bold cyan] {playlist.name}")
    console.print(f"[bold cyan]Tracks:[/bold cyan] {playlist.track_count}")
    console.print(
        f"[bold cyan]Total Duration:[/bold cyan] "
        f"{playlist.total_duration/60:.1f} minutes"
    )
    console.print(
        f"[bold cyan]Type:[/bold cyan] {'Folder' if playlist.is_folder else 'Playlist'}"
    )

    # Show first few tracks
    if playlist.tracks:
        console.print("\n[bold cyan]Sample tracks:[/bold cyan]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Artist", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Duration", justify="right")

        for track in playlist.tracks[:10]:  # Show first 10 tracks
            duration = f"{track.duration/60:.1f}m" if track.duration else "Unknown"
            table.add_row(track.artist, track.title, duration)

        if playlist.track_count > 10:
            table.add_row("...", f"and {playlist.track_count - 10} more", "")

        console.print(table)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
