<h1 align="center" >Universal DJ USB</h1>

<p align="center">
  <img src="https://raw.githubusercontent.com/juanmartin/universal-dj-usb/refs/heads/main/src/universal_dj_usb/assets/icons/icono.png" width="400" alt="Universal DJ USB Logo" />
</div>

<div align="center">

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/juanmartin/universal-dj-usb/build.yml?branch=main)](https://github.com/juanmartin/universal-dj-usb/actions)
![GitHub Release](https://img.shields.io/github/v/release/juanmartin/universal-dj-usb)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/juanmartin/universal-dj-usb/total)
[![PR's Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat)](http://makeapullrequest.com)
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-pr/juanmartin/universal-dj-usb)
![GitHub contributors](https://img.shields.io/github/contributors/juanmartin/universal-dj-usb)

A tool for converting playlists present in Rekordbox-ready USB drives to various formats including Traktor NML, M3U, and M3U8.

[![Download](https://custom-icon-badges.demolab.com/badge/-Download-blue?style=for-the-badge&logo=download&logoColor=white "Download")](https://github.com/juanmartin/universal-dj-usb/releases/latest)

</div>

## Features

- **Parse Rekordbox USB drives**: Automatically detect and parse Rekordbox database files (`.pdb`)
- **Multiple output formats**: Convert to Traktor NML, M3U, or M3U8 playlists
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Preserve metadata**: Keep track information, BPM, Key
- **Flexible paths**: Support for both relative and absolute file paths
- **Playlist filtering**: Convert specific playlists or all playlists at once
- **GUI**: Graphical user interface for easy interaction
- **CLI interface**: Easy-to-use command-line interface with rich output

## Installation (users)

There are two flavors for this tool: GUI app or CLI, both are portable 1-file executables. I try to keep feature parity on both.

1. Download the latest release from the [Releases](https://github.com/juanmartin/universal-dj-usb/releases/latest) page. Pick your OS and architecture.
2. Run the executable (GUI) or follow the CLI instructions.
3. Be free from vendor lock 👌

## Usage (opinionated)

I recommend you save the playlists in a folder inside your USB drive so that you take them with you!

Because of OS reasons, paths might differ when using this tool in macOS vs Windows, so it's also wise to keep this (portable) app in your USB drive in case you need to quickly re-generate your playlists and start playing!

My usual workflow would be:

1. Sync rekordbox playlists to USB drive.
2. Open the Universal DJ USB app.
3. Convert the ones I might use at the afters later to a folder in the same USB. 🤣
4. Profit!

## Detailed Usage

### GUI Usage

1. Launch the application. Refresh USB drives.
2. Select the USB drive containing the Rekordbox playlists (will be detected automatically).
3. Choose the desired output folder and format(s) and any specific playlists to convert.
4. Click "Convert" and wait for the process to complete.
5. Find created playlist in the specified output folder.

### CLI Usage

```bash
# Basic help and version
udj --help
udj --version

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
└── Contents/                      # Your music files
    ├── <Artist>
    │   ├── <Album>
    │   │   ├── track1.mp3
    │   │   ├── track2.mp3
    │   │   └── ...
    │   └── ...
    └── ...
```

## Output Formats

### Traktor NML (`.nml`)

- Native Traktor playlist format
- Includes (full) metadata, Key, and BPM information

### M3U (`.m3u`)

- Basic playlist format supported by most DJ software and media players
- Includes track duration and basic metadata

### M3U8 (`.m3u8`)

- Extended M3U format with UTF-8 encoding
- Includes additional metadata like album, year, genre, and BPM (_maybe not_)
- Better cross-software compatibility (except Traktor)

## Development

### Note

I have developed this with heavy use of AI agent (Claude Sonnet 4). I acknowledge the limitations and potential inaccuracies that may arise from this, but on the way I've learned a lot on how to use it wisely. I'd rather say I was the architect that told the builder what to do and closely supervised the process. All testing and validation has been done manually, as well as the engineering approaches taken were decided by me.

### Setting up for Development

```bash
# Clone the repository
git clone https://github.com/juanmartin/universal-dj-usb.git
cd universal-dj-usb

# Setup python version
pyenv local 3.11.13

# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting and formatting
uv run black src/
uv run isort src/
uv run flake8 src/
```

### Running Tests

```bash
uv run pytest
uv run pytest --cov=src/universal_dj_usb
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

## Motivation

I found myself in the situation in which someone wants to play using my equipment (Traktor) and they bring me a rekordbox-ready USB drive, so they would not have their playlists displayed in Traktor. It even happens to me as I only keep a rekordbox-ready USB to play on CDJs at hand at all times. This tool allows you to export your USB drive for CDJs only (using rekordbox) but in case you get to play with Traktor (or possibly anything else coming soon!) at the afters, you are able to convert your playlists on the fly, avoiding having duplicated audio files and just referencing them from created playlists.

## How?

This tool works by parsing the Rekordbox database file (`export.pdb`) and extracting the necessary information to create compatible playlists for other DJ software. Files are untouched. Rekordbox puts audio files in a specific folder structure, so this tool can easily locate them based on the metadata extracted from the database.

## Acknowledgments

- This project uses Kaitai Struct definitions for parsing Rekordbox PDB files
- Thanks to the guys at [Deep-Symmetry](https://github.com/Deep-Symmetry/) for reverse engineering the Rekordbox format. Check out their [crate-digger](https://github.com/Deep-Symmetry/crate-digger/tree/main). I found about this from using [Mixxx](https://github.com/mixxxdj/mixxx/tree/main) DJ software and seeing it could parse playlists from a rekordbox-ready USB. This would not be possible without their work.
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
