<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Universal DJ USB Playlist Converter - Copilot Instructions

## Project Overview

This is a clean, modern Python application that converts Rekordbox USB playlists to multiple formats (NML, M3U, M3U8). The project has been restructured to follow Python best practices with minimal dependencies and a clear architecture.

## Current Architecture (Post-Migration August 2025)

**Clean, minimal structure achieved through project restructuring:**

- **Models**: All data structures in `models.py` (Track, Playlist, PlaylistTree, ConversionConfig, ConversionResult)
- **Parser**: Single Kaitai Struct-based parser in `parser.py` (removed duplicate parsers)
- **Generators**: Modular format generators in `generators/` directory
  - `base.py`: Abstract base generator class
  - `nml.py`: Traktor NML format generator
  - `m3u.py`: Basic M3U playlist generator
  - `m3u8.py`: Extended M3U8 playlist generator
- **CLI**: Rich-enhanced command-line interface in `cli.py`
- **Kaitai**: Struct definitions in `kaitai/rekordbox_pdb.py`

**Removed components:** GUI, converter orchestration class, utils, multiple redundant parsers

## Key Technologies

- **Python 3.8.1+**: Main programming language (updated constraint for flake8 compatibility)
- **Poetry**: Dependency management and build system (single config file approach)
- **Kaitai Struct**: Direct parsing of Rekordbox PDB files (removed rekordcrate dependency)
- **Click**: CLI framework with rich integration
- **Rich**: Beautiful terminal output with progress bars, tables, and colors
- **lxml**: XML processing for NML generation
- **pathlib**: Cross-platform path handling

**Removed dependencies:** Tkinter (GUI), rekordcrate (replaced with direct Kaitai), toml, pydantic

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Use dataclasses with field defaults for data structures
- Prefer pathlib.Path over string paths
- Use logging instead of print statements
- Modular generator pattern for output formats

### Project Structure

```
src/universal_dj_usb/
├── __init__.py          # Package initialization with version info
├── models.py           # All data models (Track, Playlist, etc.)
├── parser.py           # Single Kaitai-based PDB parser
├── cli.py              # Rich-enhanced CLI interface
├── generators/         # Modular format generators
│   ├── __init__.py
│   ├── base.py         # Abstract base generator
│   ├── nml.py          # Traktor NML format
│   ├── m3u.py          # Basic M3U format
│   └── m3u8.py         # Extended M3U8 format
└── kaitai/
    ├── __init__.py
    └── rekordbox_pdb.py # Kaitai struct definition
```

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

### Build and Dependency Management

- **Poetry only**: No Makefile, shell scripts, or setup.py needed
- **pyproject.toml**: Single configuration file for everything
- **Minimal dependencies**: Only essential packages included
- **Dev dependencies**: Separated development tools (pytest, black, flake8, mypy)

## External Dependencies

### Kaitai Struct Parser

The application uses Kaitai Struct for direct PDB parsing:

- **Direct parsing**: No external CLI dependencies
- **Kaitai definition**: `kaitai/rekordbox_pdb.py` (generated from .ksy files)
- **Performance**: Fast, in-memory parsing
- **Reliability**: No subprocess calls or external tools needed

### Git Submodule

- **crate-digger**: Kaitai struct definitions for Rekordbox formats
- **Path**: `external/crate-digger` (if using submodule approach)
- **Purpose**: Source of truth for Kaitai .ksy files

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

### M3U/M3U8 Formats

- **M3U**: Basic playlist format with track paths and duration
- **M3U8**: Extended format with UTF-8 encoding and metadata
- **Cross-platform**: Works with most DJ software and media players

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

### Generator Pattern

```python
# All generators inherit from BaseGenerator
class M3UGenerator(BaseGenerator):
    def generate(self, playlist: Playlist, output_path: Path) -> ConversionResult:
        # Format-specific logic
        pass

    @property
    def file_extension(self) -> str:
        return ".m3u"
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

- CLI commands call parser and generator methods directly
- Progress reporting via Rich library
- Configuration passed as ConversionConfig objects

### Parser Integration

- Direct Kaitai Struct parsing of PDB files
- In-memory processing for better performance
- No external subprocess dependencies

### Generator Integration

- Modular generator pattern for different formats
- Each generator handles format-specific logic
- Consistent ConversionResult interface

### NML Generation

- XML generation with proper formatting
- Support for cue points and loops
- Relative path conversion for portability

## Development Notes

- The project has been completely restructured (August 2025) for cleaner architecture
- Removed GUI components to focus on CLI-first approach
- Direct Kaitai Struct parsing eliminates external dependencies
- Modular generator design makes adding new formats trivial
- Rich CLI provides excellent user experience with progress bars and tables
- Poetry-only dependency management (no Makefiles or shell scripts)
- All duplicate and debug files have been cleaned up
- Type hints and dataclasses used throughout for better code quality

## Created CLI Reference

```bash

> poetry run udj --help

Usage: udj [OPTIONS] COMMAND [ARGS]...

  Universal DJ USB Playlist Converter.

  Convert Rekordbox USB playlists to various formats (NML, M3U, M3U8).

Options:
  --debug  Enable debug output
  --help   Show this message and exit.

Commands:
  convert         Convert Rekordbox playlists to specified format(s).
  detect          Detect and validate Rekordbox data on USB drive.
  info            Get detailed information about a specific playlist.
  list-playlists  List all available playlists on the USB drive.


> poetry run udj convert --help

Usage: udj convert [OPTIONS] USB_PATH

  Convert Rekordbox playlists to specified format(s).

Options:
  -o, --output PATH               Output directory for playlist files
  -p, --playlist TEXT             Specific playlist names to convert (can be
                                  used multiple times)
  -f, --format [nml|m3u|m3u8|all]
                                  Output format
  --relative-paths / --absolute-paths
                                  Use relative or absolute file paths
  --help                          Show this message and exit.

> poetry run udj info --help

Usage: udj info [OPTIONS] USB_PATH PLAYLIST_NAME

  Get detailed information about a specific playlist.

Options:
  --help  Show this message and exit.

```
