<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Universal DJ USB Playlist Converter - Copilot Instructions

## Project Overview

This is a Python application that converts Rekordbox prepared USB playlists to Traktor's NML format. The application provides both CLI and GUI interfaces and works cross-platform (Windows, macOS, Linux).

## Architecture

- **Models**: Data structures for playlists, tracks, and cue points (`models.py`)
- **Parser**: Rekordbox database parser using the rekordcrate Rust library (`rekordbox_parser.py`)
- **Generator**: Traktor NML file generator (`nml_generator.py`)
- **Converter**: Main orchestration class (`converter.py`)
- **CLI**: Command-line interface using Click and Rich (`cli.py`)
- **GUI**: Tkinter-based graphical interface (`gui.py`)
- **Utils**: Cross-platform utilities and helpers (`utils.py`)

## Key Technologies

- **Python 3.8+**: Main programming language
- **rekordcrate**: Rust library for parsing Rekordbox database files
- **Click**: CLI framework
- **Rich**: Terminal styling and progress bars
- **Tkinter**: GUI framework (standard library)
- **lxml**: XML processing for NML generation
- **pathlib**: Cross-platform path handling

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Use dataclasses for data structures
- Prefer pathlib.Path over string paths
- Use logging instead of print statements

### Cross-Platform Considerations

- Always use pathlib.Path for file paths
- Normalize file paths with forward slashes for NML output
- Support relative paths for USB drive portability
- Handle Windows drive letters, macOS /Volumes, and Linux mount points

### Error Handling

- Use try/catch blocks for file operations
- Provide meaningful error messages to users
- Log errors with appropriate severity levels
- Return ConversionResult objects with success/failure status

### Testing

- Write unit tests for all core functionality
- Mock external dependencies (rekordcrate CLI)
- Use temporary directories for file operations
- Test cross-platform path handling

## External Dependencies

### rekordcrate Library

The application depends on the rekordcrate Rust library for parsing Rekordbox database files:

- Repository: https://github.com/Holzhaus/rekordcrate
- Used via CLI subprocess calls
- Parses PIONEER/rekordbox/export.pdb files
- Extracts playlist structure and track metadata

### rekordcrate CLI

The CLI interface for rekordcrate is used to parse Rekordbox playlists:

The CLI is built and can be run as follows:

`<path-to-repo>/rekordcrate/target/release/rekordcrate help`

The help returns the following output:

```bash
Library for parsing Pioneer Rekordbox device exports

Usage: rekordcrate <COMMAND>

Commands:
  list-playlists  List the playlist tree from a Pioneer Database (`.PDB`) file
  dump-anlz       Parse and dump a Rekordbox Analysis (`ANLZXXXX.DAT`) file
  dump-pdb        Parse and dump a Pioneer Database (`.PDB`) file
  dump-setting    Parse and dump a Pioneer Settings (`*SETTING.DAT`) file
  dump-xml        Parse and dump a Pioneer XML (`*.xml`) file
  help            Print this message or the help of the given subcommand(s)

Options:
  -h, --help     Print help
  -V, --version  Print version
```

### Rekordbox File Structure

```
USB Drive/
├── PIONEER/
│   ├── rekordbox/
│   │   └── export.pdb          # Main database file
│   └── USBANLZ/                # Analysis files (cue points, etc.)
└── Music/                      # Music files
```

### Traktor NML Format

- XML-based playlist format
- Supports track metadata, cue points, loops
- Uses relative file paths for portability
- Version 19 format compatibility

## Common Patterns

### File Path Handling

```python
# Always use pathlib
from pathlib import Path

# Normalize for cross-platform compatibility
def normalize_path(path: Path, base_path: Path = None) -> str:
    # Convert to relative path and use forward slashes
    if base_path:
        rel_path = path.relative_to(base_path)
        return str(rel_path).replace("\\", "/")
    return str(path).replace("\\", "/")
```

### Error Handling

```python
def convert_playlist(...) -> ConversionResult:
    try:
        # Conversion logic
        return ConversionResult(success=True, ...)
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return ConversionResult(success=False, error_message=str(e))
```

### Configuration Management

```python
# Use ConversionConfig dataclass
config = ConversionConfig(
    relative_paths=True,
    include_cue_points=True,
    file_naming="playlist_name"
)
```

## Integration Points

### CLI to Core

- CLI commands call converter methods
- Progress reporting via Rich library
- Configuration loaded from TOML files

### GUI to Core

- GUI uses threading for non-blocking conversion
- Progress updates via queue communication
- Tkinter widgets bound to converter methods

### Parser Integration

- Subprocess calls to rekordcrate CLI
- Parse output to extract playlist/track data
- Handle rekordcrate not being installed

### NML Generation

- XML generation with proper formatting
- Support for cue points and loops
- Relative path conversion for portability

## Development Notes

- The rekordcrate integration is currently simplified and would need proper implementation
- GUI uses threading to prevent UI blocking during conversion
- CLI supports both interactive and batch modes
- Configuration can be loaded from TOML files
- Cross-platform USB detection works but may need refinement
- NML generation follows Traktor's XML schema requirements

## Created CLI Reference

```bash

> python -m universal_dj_usb.cli --help

Usage: python -m universal_dj_usb.cli [OPTIONS] COMMAND [ARGS]...

  Universal DJ USB Playlist Converter - Convert Rekordbox playlists to Traktor
  NML format.

Options:
  --debug        Enable debug output
  --config PATH  Path to configuration file
  --help         Show this message and exit.

Commands:
  config-info      Display current configuration information.
  convert          Convert Rekordbox playlists to Traktor NML format.
  detect           Detect USB drives with Rekordbox exports.
  export-playlist  Export a specific playlist to a text file for manual...
  info             Get detailed information about a specific playlist.
  list-playlists   List all available playlists on a USB drive.


> python -m universal_dj_usb.cli convert --help

Usage: python -m universal_dj_usb.cli convert [OPTIONS] USB_PATH

  Convert Rekordbox playlists to various formats (NML, M3U, M3U8).

Options:
  -o, --output DIRECTORY          Output directory for playlist files
  -p, --playlist TEXT             Specific playlist names to convert
  -l, --list-only                 List available playlists only
  -f, --format [nml|m3u|m3u8|all]
                                  Output format: nml (Traktor), m3u (basic),
                                  m3u8 (extended), or all formats
  --help                          Show this message and exit.

> python -m universal_dj_usb.cli export-playlist --help

Usage: python -m universal_dj_usb.cli export-playlist [OPTIONS] USB_PATH
                                                      PLAYLIST_NAME

  Export a specific playlist to a text file for manual verification.

Options:
  -o, --output PATH  Output file path
  --help             Show this message and exit.

```
