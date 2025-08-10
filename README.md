# Universal DJ USB Playlist Converter

## WARNING: Este proyecto está full vibecoded con Claude Sonnet 4 a la hora de describir esto

Igual muchos cambios a mano y el debugging y testeo es manual.
PRs bienvenidos, habran issues, hablemos, hagamos.

A modern Python tool for converting Rekordbox USB playlists to various formats including Traktor NML, M3U, and M3U8.

## Features

- **Parse Rekordbox USB drives**: Automatically detect and parse Rekordbox database files (`.pdb`)
- **Multiple output formats**: Convert to Traktor NML, M3U, or M3U8 playlists
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Preserve metadata**: Keep track information, cue points, and BPM data
- **Flexible paths**: Support for both relative and absolute file paths
- **CLI interface**: Easy-to-use command-line interface with rich output

## Installation

### Requirements

- Python 3.8+
- Poetry (recommended) or pip

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/universal-dj-usb.git
cd universal-dj-usb

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/universal-dj-usb.git
cd universal-dj-usb

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -e .
```

## Usage

### Basic Usage

```bash
# List available playlists on a USB drive
udj list-playlists /path/to/usb/drive

# Convert all playlists to Traktor NML format
udj convert /path/to/usb/drive

# Convert specific playlists to M3U format
udj convert /path/to/usb/drive -p "My Playlist" -p "Another Playlist" -f m3u

# Convert to all formats
udj convert /path/to/usb/drive -f all -o ./output
```

### Commands

#### `detect`

Detect and validate Rekordbox data on a USB drive.

```bash
udj detect /path/to/usb/drive
```

#### `list-playlists`

List all available playlists on the USB drive.

```bash
udj list-playlists /path/to/usb/drive
```

#### `convert`

Convert playlists to specified format(s).

```bash
udj convert [OPTIONS] USB_PATH

Options:
  -o, --output PATH           Output directory for playlist files
  -p, --playlist TEXT         Specific playlist names to convert (multiple allowed)
  -f, --format [nml|m3u|m3u8|all]  Output format (default: nml)
  --relative-paths/--absolute-paths  Use relative or absolute file paths (default: relative)
```

#### `info`

Get detailed information about a specific playlist.

```bash
udj info /path/to/usb/drive "Playlist Name"
```

### Examples

```bash
# Convert all playlists to Traktor NML format
udj convert /Volumes/USB_DRIVE -f nml -o ~/TraktorPlaylists

# Convert specific playlists to M3U8 format
udj convert /Volumes/USB_DRIVE -p "House Music" -p "Techno Sets" -f m3u8

# Get information about a playlist
udj info /Volumes/USB_DRIVE "My Weekend Mix"
```

## File Structure

The tool expects a standard Rekordbox USB drive structure:

```
USB Drive/
├── PIONEER/
│   └── rekordbox/
│       └── export.pdb          # Main database file
└── Music/                      # Your music files
    ├── track1.mp3
    ├── track2.mp3
    └── ...
```

## Output Formats

### Traktor NML (`.nml`)

- Native Traktor playlist format
- Includes full metadata, cue points, and BPM information
- Compatible with Traktor Pro versions

### M3U (`.m3u`)

- Basic playlist format supported by most DJ software and media players
- Includes track duration and basic metadata

### M3U8 (`.m3u8`)

- Extended M3U format with UTF-8 encoding
- Includes additional metadata like album, year, genre, and BPM
- Better cross-platform compatibility

## Development

### Setting up for Development

```bash
# Clone the repository
git clone https://github.com/yourusername/universal-dj-usb.git
cd universal-dj-usb

# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run linting and formatting
poetry run black src/
poetry run isort src/
poetry run flake8 src/
```

### Running Tests

```bash
poetry run pytest
poetry run pytest --cov=src/universal_dj_usb
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This project uses Kaitai Struct definitions for parsing Rekordbox PDB files
- Thanks to the Pioneer DJ community for reverse engineering the Rekordbox format
- Built with Python, Click, Rich, and lxml

## Troubleshooting

### Common Issues

1. **"No Rekordbox database found"**
   - Ensure your USB drive contains a proper Rekordbox export
   - Check that the `PIONEER/rekordbox/export.pdb` file exists

2. **"Failed to parse database"**
   - The PDB file might be corrupted or from an unsupported Rekordbox version
   - Try exporting again from Rekordbox

3. **File paths not working**
   - Use the `--relative-paths` option for better cross-platform compatibility
   - Ensure your music files are in the expected location on the USB drive

### Getting Help

- Open an issue on GitHub with detailed information about your problem
- Include the USB drive structure and any error messages
- Specify your operating system and Python version
