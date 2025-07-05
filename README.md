# Universal DJ USB Playlist Converter

## WARNING: Este proyecto está full vibecoded con Claude Sonnet 4 a la hora de describir esto

PRs bienvenidos, habran issues, hablemos, hagamos.

## Brief

A powerful, cross-platform application that converts Rekordbox prepared USB playlists to Traktor's NML format, making your music library compatible across different DJ software platforms.

## Features

- **Universal Compatibility**: Convert Rekordbox playlists to Traktor NML format
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Smart Path Handling**: Automatically handles relative paths and different OS slash conventions
- **Dual Interface**: Command-line tool for power users and GUI for everyone else
- **USB Drive Support**: Directly reads from Rekordbox prepared USB drives
- **Batch Processing**: Convert multiple playlists at once
- **Metadata Preservation**: Keeps track information, cue points, and playlist structure

## Installation

### From PyPI (Recommended)

```bash
pip install universal-dj-usb
```

### From Source

```bash
git clone https://github.com/universal-dj-usb/universal-dj-usb.git
cd universal-dj-usb
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Convert all playlists from a USB drive
universal-dj-usb /path/to/usb/drive --output /path/to/output/folder

# Convert specific playlists
universal-dj-usb /path/to/usb/drive --playlist "House Music" --playlist "Techno"

# Use short command
udj /path/to/usb/drive -o /path/to/output
```

### Graphical User Interface

```bash
# Launch GUI
universal-dj-usb-gui
# or
udj-gui
```

The GUI provides a user-friendly interface where you can:

- Select your USB drive
- Choose which playlists to convert
- Set output directory
- Monitor conversion progress

## Requirements

- Python 3.8 or higher
- Rekordbox prepared USB drive
- Rust toolchain (for rekordcrate library)

## Dependencies

The application uses the powerful [rekordcrate](https://github.com/Holzhaus/rekordcrate) Rust library to parse Rekordbox database files and extract playlist information.

## How It Works

1. **USB Detection**: Automatically detects Rekordbox prepared USB drives
2. **Database Parsing**: Uses rekordcrate to parse the `PIONEER/rekordbox/export.pdb` file
3. **Playlist Extraction**: Extracts playlist tree structure and track relationships
4. **Path Normalization**: Converts absolute paths to relative paths compatible with different OS
5. **NML Generation**: Creates Traktor-compatible NML files with proper XML structure

## File Structure

```text
USB Drive/
├── PIONEER/
│   ├── rekordbox/
│   │   └── export.pdb          # Main database file
│   └── USBANLZ/                # Analysis files
└── Music/                      # Your music files
```

## Output Format

The converter generates `.nml` files that can be imported directly into Traktor Pro. Each playlist becomes a separate NML file with:

- Playlist name and structure
- Track metadata (title, artist, album, etc.)
- Relative file paths for cross-platform compatibility
- Cue points and loops (if available)

## Advanced Usage

### Configuration File

Create a `config.toml` file to customize conversion settings:

```toml
[conversion]
relative_paths = true
preserve_folder_structure = true
include_cue_points = true
include_loops = true

[output]
file_naming = "playlist_name"  # or "sequential"
encoding = "utf-8"
```

### Batch Processing

```bash
# Process multiple USB drives
for drive in /media/usb*; do
    udj "$drive" -o "/home/user/playlists/$(basename "$drive")"
done
```

## Troubleshooting

### Common Issues

1. **"No Rekordbox database found"**: Ensure the USB drive was prepared with Rekordbox
2. **"Permission denied"**: Run with appropriate permissions to read the USB drive
3. **"Invalid playlist format"**: Check if the playlist contains unsupported characters

### Debug Mode

```bash
udj /path/to/usb --debug --verbose
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [rekordcrate](https://github.com/Holzhaus/rekordcrate) - Rust library for parsing Rekordbox exports
- [Deep Symmetry](https://github.com/Deep-Symmetry) - Pioneer format research
- DJ community for testing and feedback

## Support

- 📧 Email: [support@universal-dj-usb.com](mailto:support@universal-dj-usb.com)
- 🐛 Issues: [GitHub Issues](https://github.com/universal-dj-usb/universal-dj-usb/issues)
- 💬 Discord: [Join our community](https://discord.gg/universal-dj-usb)

---

Made with ❤️ by DJs, for DJs
