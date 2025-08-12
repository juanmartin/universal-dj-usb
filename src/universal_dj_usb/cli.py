"""Command-line interface for the Universal DJ USB playlist converter."""

import logging
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel

from .parser import RekordboxParser
from .models import ConversionConfig, Playlist
from .generators import NMLGenerator, M3UGenerator, M3U8Generator

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
            console.print(f"[green]✓ Successfully parsed database[/green]")
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
    help="Use extended M3U format with metadata (default) or simple format (paths only)",
)
@click.option(
    "--m3u-absolute-paths/--m3u-relative-paths",
    default=False,
    help="Use absolute paths in M3U files instead of relative paths",
)
@click.pass_context
def convert(
    ctx: click.Context,
    usb_path: Path,
    output: Optional[Path],
    playlist: tuple,
    format: str,
    relative_paths: bool,
    use_format_suffix: bool,
    m3u_extended: bool,
    m3u_absolute_paths: bool,
) -> None:
    """Convert Rekordbox playlists to specified format(s)."""
    debug = ctx.obj.get("debug", False)

    # Set default output path
    if output is None:
        output = Path.cwd() / "converted_playlists"

    console.print(f"[bold blue]Converting playlists from:[/bold blue] {usb_path}")
    console.print(f"[bold blue]Output directory:[/bold blue] {output}")
    console.print(f"[bold blue]Format:[/bold blue] {format}")

    # Find and parse PDB
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

    # Filter playlists if specified
    playlists_to_convert = []
    if playlist:
        for name in playlist:
            found_playlist = playlist_tree.get_playlist_by_name(name)
            if found_playlist:
                playlists_to_convert.append(found_playlist)
            else:
                console.print(f"[yellow]Warning: Playlist '{name}' not found[/yellow]")
    else:
        # Convert all playlists (excluding folders)
        playlists_to_convert = [
            pl
            for pl in playlist_tree.all_playlists.values()
            if not pl.is_folder and pl.track_count > 0
        ]

    if not playlists_to_convert:
        console.print("[yellow]No playlists to convert[/yellow]")
        return

    # Enhance tracks with file metadata only for playlists being converted
    enhanced_playlists = []
    for playlist_obj in playlists_to_convert:
        enhanced_playlist = parser.enhance_playlist_tracks(playlist_obj, usb_path)
        enhanced_playlists.append(enhanced_playlist)

    # Create configuration
    config = ConversionConfig(
        relative_paths=relative_paths,
        output_format=format.lower(),
        use_format_suffix=use_format_suffix,
        m3u_extended=m3u_extended,
        m3u_absolute_paths=m3u_absolute_paths,
    )

    # Create generators
    generators = []
    if format.lower() == "all":
        generators = [NMLGenerator(config), M3UGenerator(config), M3U8Generator(config)]
    elif format.lower() == "nml":
        generators = [NMLGenerator(config)]
    elif format.lower() == "m3u":
        generators = [M3UGenerator(config)]
    elif format.lower() == "m3u8":
        generators = [M3U8Generator(config)]

    # Convert playlists
    output.mkdir(parents=True, exist_ok=True)

    with Progress() as progress:
        task = progress.add_task(
            "Converting playlists...", total=len(enhanced_playlists) * len(generators)
        )

        results = []
        for playlist_obj in enhanced_playlists:
            for generator in generators:
                # Construct the filename like the GUI does
                filename = generator._sanitize_filename(playlist_obj.name)

                # Add format suffix if requested (before the extension)
                if config.use_format_suffix:
                    # Get the format name without the dot (e.g., "nml", "m3u", "m3u8")
                    format_name = generator.file_extension.lstrip(".")
                    filename = f"{filename}_{format_name}"

                # Add the file extension
                filename = f"{filename}{generator.file_extension}"

                # Create the full output path
                output_path = output / filename

                result = generator.generate(playlist_obj, output_path, usb_path)
                results.append(result)

                if result.success:
                    console.print(
                        f"[green]✓[/green] {playlist_obj.name} → {result.output_file.name}"
                    )
                    # Only show warnings in debug mode
                    if debug and result.warnings:
                        for warning in result.warnings:
                            console.print(f"  [yellow]⚠[/yellow] {warning}")
                else:
                    console.print(
                        f"[red]✗[/red] {playlist_obj.name}: {result.error_message}"
                    )

                progress.advance(task)

    # Improved Summary
    successful = sum(1 for r in results if r.success)
    total = len(results)
    failed = total - successful

    console.print()
    if successful == total:
        console.print(
            f"[bold green]✅ Successfully converted {successful} playlist{'s' if successful != 1 else ''}[/bold green]"
        )
    else:
        console.print(
            f"[yellow]⚠ Converted {successful}/{total} playlists ({failed} failed)[/yellow]"
        )

    # Show basic info for each successful conversion
    for result in results:
        if result.success:
            console.print(
                f"[cyan]📁 {result.playlist_name}[/cyan]: {result.track_count} tracks → {result.output_file.name}"
            )

    console.print(f"[dim]Output directory: {output}[/dim]")

    # Debug info
    if debug:
        console.print(f"\n[dim]Debug Info:[/dim]")
        console.print(f"[dim]• Input path: {usb_path}[/dim]")
        console.print(f"[dim]• Format: {format}[/dim]")
        console.print(f"[dim]• Relative paths: {relative_paths}[/dim]")
        console.print(f"[dim]• Use format suffix: {use_format_suffix}[/dim]")
        if format.lower() in ["m3u", "m3u8", "all"]:
            console.print(f"[dim]• M3U extended format: {m3u_extended}[/dim]")
            console.print(f"[dim]• M3U absolute paths: {m3u_absolute_paths}[/dim]")
        if any(r.warnings for r in results):
            console.print(
                f"[dim]• Total warnings: {sum(len(r.warnings) for r in results)}[/dim]"
            )


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
        f"[bold cyan]Total Duration:[/bold cyan] {playlist.total_duration/60:.1f} minutes"
    )
    console.print(
        f"[bold cyan]Type:[/bold cyan] {'Folder' if playlist.is_folder else 'Playlist'}"
    )

    # Show first few tracks
    if playlist.tracks:
        console.print("\\n[bold cyan]Sample tracks:[/bold cyan]")
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
