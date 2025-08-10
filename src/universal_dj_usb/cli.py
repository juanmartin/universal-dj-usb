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
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


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
            playlist_tree = parser.get_playlists()
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

    playlist_tree = parser.get_playlists()

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
def convert(
    usb_path: Path,
    output: Optional[Path],
    playlist: tuple,
    format: str,
    relative_paths: bool,
) -> None:
    """Convert Rekordbox playlists to specified format(s)."""
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

    playlist_tree = parser.get_playlists()

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

    # Create configuration
    config = ConversionConfig(
        relative_paths=relative_paths, output_format=format.lower()
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
            "Converting playlists...", total=len(playlists_to_convert) * len(generators)
        )

        results = []
        for playlist_obj in playlists_to_convert:
            for generator in generators:
                result = generator.generate(playlist_obj, output, usb_path)
                results.append(result)

                if result.success:
                    console.print(
                        f"[green]✓[/green] {playlist_obj.name} → {result.output_file.name}"
                    )
                    if result.warnings:
                        for warning in result.warnings:
                            console.print(f"  [yellow]⚠[/yellow] {warning}")
                else:
                    console.print(
                        f"[red]✗[/red] {playlist_obj.name}: {result.error_message}"
                    )

                progress.advance(task)

    # Summary
    successful = sum(1 for r in results if r.success)
    total = len(results)

    console.print()
    console.print(
        Panel(
            f"[bold green]Conversion complete![/bold green]\\n"
            f"Successfully converted: {successful}/{total}\\n"
            f"Output directory: {output}",
            title="Summary",
        )
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

    playlist_tree = parser.get_playlists()
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
