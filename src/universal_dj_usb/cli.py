"""Command-line interface for the Universal DJ USB playlist converter."""

import click
import logging
from pathlib import Path
from typing import Optional, List
import sys
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .converter import RekordboxToTraktorConverter
from .models import ConversionConfig
from .utils import load_config, get_platform_specific_paths

console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.option(
    "--config", type=click.Path(exists=True), help="Path to configuration file"
)
@click.pass_context
def cli(ctx: click.Context, debug: bool, config: Optional[str]) -> None:
    """Universal DJ USB Playlist Converter - Convert Rekordbox playlists to various formats (NML, M3U, M3U8)."""
    # Set up logging
    log_level = "DEBUG" if debug else "INFO"
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load configuration
    if config:
        config_data = load_config(Path(config))
    else:
        # Try to load default config
        paths = get_platform_specific_paths()
        default_config_path = paths["config"] / "config.toml"
        config_data = load_config(default_config_path)

    # Create conversion config
    conversion_config = ConversionConfig()
    if "conversion" in config_data:
        conversion_config = ConversionConfig.from_dict(config_data["conversion"])

    # Store in context
    ctx.ensure_object(dict)
    ctx.obj["config"] = conversion_config
    ctx.obj["debug"] = debug


@cli.command()
@click.argument(
    "usb_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=False),
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Output directory for playlist files",
)
@click.option(
    "--playlist", "-p", multiple=True, help="Specific playlist names to convert"
)
@click.option("--list-only", "-l", is_flag=True, help="List available playlists only")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["nml", "m3u", "m3u8", "all"], case_sensitive=False),
    default="nml",
    help="Output format: nml (Traktor), m3u (basic), m3u8 (extended), or all formats",
)
@click.pass_context
def convert(
    ctx: click.Context,
    usb_path: str,
    output: Optional[str],
    playlist: tuple,
    list_only: bool,
    format: str,
) -> None:
    """Convert Rekordbox playlists to various formats (NML, M3U, M3U8)."""

    usb_drive_path = Path(usb_path)
    config = ctx.obj["config"]

    # Update the output format in the config
    config.output_format = format.lower()

    # Initialize converter
    converter = RekordboxToTraktorConverter(config)

    # Validate USB drive
    if not converter.validate_usb_drive(usb_drive_path):
        rprint(
            "[red]Error: No valid Rekordbox export found on the specified drive.[/red]"
        )
        rprint(f"Expected to find: {usb_drive_path}/PIONEER/rekordbox/export.pdb")
        sys.exit(1)

    rprint(f"[green]Found valid Rekordbox export at: {usb_drive_path}[/green]")

    # List playlists if requested
    if list_only:
        _list_playlists(converter, usb_drive_path)
        return

    # Set up output directory
    if not output:
        output = Path.cwd() / "converted_playlists"
    else:
        output = Path(output)

    output.mkdir(parents=True, exist_ok=True)

    # Convert playlists
    playlist_filter = list(playlist) if playlist else None

    rprint(f"[blue]Converting playlists to: {output}[/blue]")

    if playlist_filter:
        rprint(
            f"[blue]Converting specific playlists: {', '.join(playlist_filter)}[/blue]"
        )
    else:
        rprint("[blue]Converting all playlists[/blue]")

    # Show progress and convert
    with Progress() as progress:
        task = progress.add_task("[green]Converting...", total=100)

        results = converter.convert_all_playlists(
            usb_drive_path, output, playlist_filter
        )

        progress.update(task, completed=100)

    # Display results
    _display_conversion_results(results)


@cli.command()
@click.argument(
    "usb_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=False),
)
def list_playlists(usb_path: str) -> None:
    """List all available playlists on a USB drive."""

    usb_drive_path = Path(usb_path)
    converter = RekordboxToTraktorConverter()

    if not converter.validate_usb_drive(usb_drive_path):
        rprint(
            "[red]Error: No valid Rekordbox export found on the specified drive.[/red]"
        )
        sys.exit(1)

    _list_playlists(converter, usb_drive_path)


@cli.command()
def detect() -> None:
    """Detect USB drives with Rekordbox exports."""

    converter = RekordboxToTraktorConverter()
    drives = converter.detect_usb_drives()

    if not drives:
        rprint("[yellow]No USB drives with Rekordbox exports found.[/yellow]")
        rprint("\nMake sure:")
        rprint("1. USB drive is connected")
        rprint("2. Drive was prepared with Rekordbox")
        rprint("3. PIONEER/rekordbox/export.pdb file exists")
        return

    table = Table(title="Detected USB Drives with Rekordbox Exports")
    table.add_column("Drive Path", style="cyan")
    table.add_column("Export File", style="green")

    for drive in drives:
        export_file = drive / "PIONEER" / "rekordbox" / "export.pdb"
        table.add_row(str(drive), str(export_file))

    console.print(table)


@cli.command()
@click.argument(
    "usb_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.argument("playlist_name")
def info(usb_path: str, playlist_name: str) -> None:
    """Get detailed information about a specific playlist."""

    usb_drive_path = Path(usb_path)
    converter = RekordboxToTraktorConverter()

    if not converter.validate_usb_drive(usb_drive_path):
        rprint(
            "[red]Error: No valid Rekordbox export found on the specified drive.[/red]"
        )
        sys.exit(1)

    playlist_info = converter.get_playlist_info(usb_drive_path, playlist_name)

    if not playlist_info:
        rprint(f"[red]Playlist '{playlist_name}' not found.[/red]")
        sys.exit(1)

    # Display playlist information
    panel_content = f"""
[bold]Name:[/bold] {playlist_info['name']}
[bold]Tracks:[/bold] {playlist_info['track_count']}
[bold]Duration:[/bold] {playlist_info['total_duration']:.1f} seconds
[bold]Type:[/bold] {'Folder' if playlist_info['is_folder'] else 'Playlist'}
"""

    console.print(
        Panel(panel_content, title=f"Playlist: {playlist_name}", expand=False)
    )

    # Display track list
    if playlist_info["tracks"]:
        table = Table(title="Tracks")
        table.add_column("Title", style="cyan")
        table.add_column("Artist", style="green")
        table.add_column("Album", style="yellow")
        table.add_column("Duration", style="magenta")

        for track in playlist_info["tracks"][:20]:  # Limit to first 20 tracks
            duration = f"{track['duration']:.1f}s" if track["duration"] else "Unknown"
            table.add_row(
                track["title"], track["artist"], track["album"] or "Unknown", duration
            )

        if len(playlist_info["tracks"]) > 20:
            table.add_row(
                "...",
                "...",
                "...",
                f"({len(playlist_info['tracks']) - 20} more tracks)",
            )

        console.print(table)


@cli.command()
def config_info() -> None:
    """Display current configuration information."""

    paths = get_platform_specific_paths()
    config_path = paths["config"] / "config.toml"
    data_path = paths["data"]

    rprint(f"[bold]Configuration Directory:[/bold] {paths['config']}")
    rprint(f"[bold]Data Directory:[/bold] {data_path}")
    rprint(f"[bold]Configuration File:[/bold] {config_path}")
    rprint(f"[bold]Config Exists:[/bold] {'Yes' if config_path.exists() else 'No'}")

    if config_path.exists():
        config_data = load_config(config_path)
        rprint(f"[bold]Configuration:[/bold]")
        for section, values in config_data.items():
            rprint(f"  [cyan]{section}:[/cyan]")
            for key, value in values.items():
                rprint(f"    {key}: {value}")


@cli.command()
@click.argument("usb_path", type=click.Path(exists=True, file_okay=False))
@click.argument("playlist_name", type=str)
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.pass_context
def export_playlist(ctx, usb_path, playlist_name, output):
    """Export a specific playlist to a text file for manual verification."""
    from pathlib import Path
    from rich.console import Console

    console = Console()

    try:
        # Import parser here to avoid circular imports
        from .advanced_pdb_parser import AdvancedPDBParser

        usb_path = Path(usb_path)

        # Check if PDB file exists
        pdb_file = usb_path / "PIONEER" / "rekordbox" / "export.pdb"
        if not pdb_file.exists():
            console.print(f"❌ PDB file not found: {pdb_file}", style="red")
            return

        # Set output file
        if output:
            output_file = Path(output)
        else:
            output_file = Path(f"{playlist_name.replace(' ', '_')}.txt")

        console.print(f"📁 Parsing PDB file: {pdb_file}")

        # Parse with advanced parser
        parser = AdvancedPDBParser(pdb_file, usb_path)

        console.print(f"📝 Exporting playlist '{playlist_name}' to {output_file}")

        # Export playlist
        success = parser.export_playlist_to_txt(playlist_name, output_file)

        if success:
            console.print(
                f"✅ Playlist exported successfully to {output_file}", style="green"
            )
        else:
            console.print(f"❌ Failed to export playlist", style="red")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        if ctx.obj["debug"]:
            import traceback

            console.print(traceback.format_exc(), style="red")


def _list_playlists(
    converter: RekordboxToTraktorConverter, usb_drive_path: Path
) -> None:
    """Helper function to list playlists."""

    playlists = converter.list_playlists(usb_drive_path)

    if not playlists:
        rprint("[yellow]No playlists found on the USB drive.[/yellow]")
        return

    table = Table(title=f"Playlists on {usb_drive_path}")
    table.add_column("Playlist Name", style="cyan")
    table.add_column("Type", style="green")

    for playlist_name in playlists:
        table.add_row(playlist_name, "Playlist")

    console.print(table)
    rprint(f"\n[blue]Found {len(playlists)} playlists[/blue]")


def _display_conversion_results(results: List) -> None:
    """Display the results of playlist conversion."""

    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    # Summary
    rprint(f"\n[bold green]Conversion Complete![/bold green]")
    rprint(f"[green]Successful:[/green] {len(successful)}")
    rprint(f"[red]Failed:[/red] {len(failed)}")

    # Successful conversions table
    if successful:
        table = Table(title="Successfully Converted Playlists")
        table.add_column("Playlist", style="cyan")
        table.add_column("Tracks", style="green")
        table.add_column("Output File", style="yellow")

        for result in successful:
            table.add_row(
                result.playlist_name,
                str(result.track_count),
                str(result.output_file.name) if result.output_file else "Unknown",
            )

        console.print(table)

    # Failed conversions
    if failed:
        rprint(f"\n[bold red]Failed Conversions:[/bold red]")
        for result in failed:
            rprint(f"[red]❌ {result.playlist_name}:[/red] {result.error_message}")


def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        rprint("\n[yellow]Conversion cancelled by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        rprint(f"[red]Unexpected error: {e}[/red]")
        if logger.isEnabledFor(logging.DEBUG):
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
