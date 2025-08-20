"""
PySide6-based GUI for Universal DJ USB Playlist Converter.
"""

import sys
import logging
import threading
import signal
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QComboBox,
    QTextEdit,
    QProgressBar,
    QFileDialog,
    QGroupBox,
    QScrollArea,
    QFrame,
    QSplitter,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
    QStatusBar,
    QSpinBox,
    QGridLayout,
    QRadioButton,
    QHeaderView,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap, QPalette, QAction

import psutil
from typing import Optional

from . import __version__
from .parser import RekordboxParser
from .models import ConversionConfig, Playlist, ConversionResult, PlaylistTree
from .generators import NMLGenerator, M3UGenerator, M3U8Generator


@dataclass
class USBDriveInfo:
    """Information about a detected USB drive."""

    path: Path
    label: str
    size: int
    free_space: int
    has_rekordbox: bool

    def __str__(self):
        size_gb = self.size / (1024**3)
        rekordbox_status = "✓" if self.has_rekordbox else "✗"
        return f"{self.label} ({size_gb:.1f}GB) - Rekordbox: {rekordbox_status}"


class PlaylistParsingWorker(QThread):
    """Worker thread for parsing Rekordbox playlists."""

    parsing_progress = Signal(str)  # Status message
    parsing_complete = Signal(object)  # PlaylistTree
    parsing_error = Signal(str)  # Error message

    def __init__(self, usb_path: Path):
        super().__init__()
        self.usb_path = usb_path

    def run(self):
        """Parse the Rekordbox database."""
        try:
            self.parsing_progress.emit("Initializing parser...")
            parser = RekordboxParser()

            self.parsing_progress.emit("Loading Rekordbox database...")
            playlist_tree = parser.parse_playlists(self.usb_path)

            self.parsing_progress.emit("Parsing complete!")
            self.parsing_complete.emit(playlist_tree)
        except Exception as e:
            self.parsing_error.emit(f"Failed to parse playlists: {str(e)}")


class ConversionWorker(QThread):
    """Worker thread for converting playlists."""

    conversion_progress = Signal(str, int)  # message, progress_percentage
    conversion_complete = Signal(list)  # List[ConversionResult]

    def __init__(
        self,
        playlists: List[Playlist],
        config: ConversionConfig,
        output_dir: Path,
        usb_path: Path,
        parser: RekordboxParser = None,
    ):
        super().__init__()
        self.playlists = playlists
        self.config = config
        self.output_dir = output_dir
        self.usb_path = usb_path
        self.parser = parser

    def run(self):
        """Convert the selected playlists."""
        results = []
        total_playlists = len(self.playlists)

        # Enhance playlists with file metadata if parser is available
        enhanced_playlists = []
        if self.parser:
            self.conversion_progress.emit("Enhancing track metadata...", 5)
            for playlist in self.playlists:
                enhanced_playlist = self.parser.enhance_playlist_tracks(
                    playlist, self.usb_path
                )
                enhanced_playlists.append(enhanced_playlist)
        else:
            enhanced_playlists = self.playlists

        # Create generators based on format
        generators = []
        if self.config.output_format in ["nml", "all"]:
            generators.append(NMLGenerator(self.config))
        if self.config.output_format in ["m3u", "all"]:
            generators.append(M3UGenerator(self.config))
        if self.config.output_format in ["m3u8", "all"]:
            generators.append(M3U8Generator(self.config))

        for i, playlist in enumerate(enhanced_playlists):
            self.conversion_progress.emit(
                f"Converting '{playlist.name}'...", int((i / total_playlists) * 100)
            )

            for generator in generators:
                try:
                    # Generate output filename
                    filename = generator._sanitize_filename(playlist.name)

                    # Add format suffix if requested (before the extension)
                    if self.config.use_format_suffix:
                        # Get the format name without the dot (e.g., "nml", "m3u", "m3u8")
                        format_name = generator.file_extension.lstrip(".")
                        filename = f"{filename}_{format_name}"

                    # Add the file extension
                    filename = f"{filename}{generator.file_extension}"

                    output_path = self.output_dir / filename
                    result = generator.generate(playlist, output_path, self.usb_path)
                    results.append(result)

                except Exception as e:
                    results.append(
                        ConversionResult(
                            success=False,
                            playlist_name=playlist.name,
                            error_message=str(e),
                        )
                    )

        self.conversion_progress.emit("Conversion complete!", 100)
        self.conversion_complete.emit(results)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal DJ USB Playlist Converter")
        self.setMinimumSize(1000, 700)

        # Data
        self.current_usb_path: Optional[Path] = None
        self.playlist_tree: Optional[PlaylistTree] = None
        self.selected_playlists: Dict[str, Playlist] = {}
        self.available_drives: List[USBDriveInfo] = []
        self.current_parser: Optional[RekordboxParser] = None

        # Workers - only conversion worker, USB and parsing are now synchronous
        self.conversion_worker = None

        # Setup UI first
        self._setup_ui()
        self._setup_status_bar()

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Log initial message
        self._log_message("Universal DJ USB Playlist Converter started")
        self._log_message("Click 'Refresh USB Drives' button to scan for drives")

        # Don't start USB detection automatically - let user trigger it
        # This avoids threading issues on startup

    def __del__(self):
        """Destructor to ensure threads are properly stopped."""
        # No USB worker to stop anymore - using direct method calls
        pass

    def _setup_ui(self):
        """Setup the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - USB and Playlists
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel - Options and Output
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([500, 500])

    def _create_left_panel(self) -> QWidget:
        """Create the left panel with USB detection and playlist list."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # USB Drive Section
        usb_group = QGroupBox("USB Drives")
        usb_layout = QVBoxLayout(usb_group)

        self.usb_label = QLabel("Click 'Refresh USB Drives' to scan for drives")
        # Use extra spacing between lines for multi-line text
        self.usb_label.setStyleSheet("color: #666; font-style: italic;")
        self.usb_label.setMinimumHeight(40)
        usb_layout.addWidget(self.usb_label)

        # USB drive picker
        drive_picker_layout = QHBoxLayout()
        drive_picker_layout.addWidget(QLabel("Select Drive:"))
        self.usb_drive_combo = QComboBox()
        # Make the combo box expand to fill available space, but not push out the label
        self.usb_drive_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.usb_drive_combo.currentTextChanged.connect(self._on_usb_drive_selected)
        self.usb_drive_combo.setEnabled(False)
        drive_picker_layout.addWidget(self.usb_drive_combo)
        usb_layout.addLayout(drive_picker_layout)

        self.refresh_button = QPushButton("Refresh USB Drives")
        self.refresh_button.clicked.connect(self._refresh_usb_drives)
        usb_layout.addWidget(self.refresh_button)

        layout.addWidget(usb_group)

        # Playlists Section
        playlist_group = QGroupBox("Playlists")
        playlist_layout = QVBoxLayout(playlist_group)

        # Playlist tree
        self.playlist_tree_widget = QTreeWidget()
        self.playlist_tree_widget.setHeaderLabels(["Playlist", "Tracks", "Order"])
        self.playlist_tree_widget.setSortingEnabled(True)
        self.playlist_tree_widget.itemChanged.connect(
            self._on_playlist_selection_changed
        )

        # Configure column widths - Playlist should be wider than Tracks
        header = self.playlist_tree_widget.header()
        header.setStretchLastSection(False)  # Don't auto-stretch the last column
        header.resizeSection(0, 250)  # Playlist column - wider for longer names
        header.resizeSection(1, 60)  # Tracks column - narrower, just for numbers
        header.resizeSection(2, 60)  # Order column - narrower, just for numbers

        # Set resize modes
        header.setSectionResizeMode(
            0, QHeaderView.Interactive
        )  # Playlist - user can resize
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # Tracks - fixed width
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Order - fixed width

        playlist_layout.addWidget(self.playlist_tree_widget)

        # Select all/none buttons
        button_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self._select_all_playlists)
        self.select_all_button.setEnabled(False)

        self.select_none_button = QPushButton("Select None")
        self.select_none_button.clicked.connect(self._select_no_playlists)
        self.select_none_button.setEnabled(False)

        button_layout.addWidget(self.select_all_button)
        button_layout.addWidget(self.select_none_button)
        playlist_layout.addLayout(button_layout)

        layout.addWidget(playlist_group)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right panel with options and conversion."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Create tabs for different sections
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # Conversion Options Tab
        options_tab = self._create_options_tab()
        tab_widget.addTab(options_tab, "Conversion Options")

        # Output Tab
        output_tab = self._create_output_tab()
        tab_widget.addTab(output_tab, "Output & Logs")

        return panel

    def _create_options_tab(self) -> QWidget:
        """Create the conversion options tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Output Directory
        output_group = QGroupBox("Output Settings")
        output_layout = QGridLayout(output_group)

        # First row: Label and Browse button
        output_layout.addWidget(QLabel("Output Directory:"), 0, 0)
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_output_directory)
        output_layout.addWidget(self.browse_button, 0, 1)

        # Second row: Full-width path display
        self.output_dir_label = QLabel("No directory selected")
        self.output_dir_label.setStyleSheet("color: #666; font-style: italic;")
        self.output_dir_label.setWordWrap(True)  # Enable word wrapping for long paths
        self.output_dir_label.setMinimumHeight(
            40
        )  # Fixed height to prevent layout shifting
        self.output_dir_label.setMaximumHeight(
            80
        )  # Maximum height to contain very long paths
        self.output_dir_label.setAlignment(
            Qt.AlignTop | Qt.AlignLeft
        )  # Align text to top-left
        output_layout.addWidget(self.output_dir_label, 1, 0, 1, 2)  # Span both columns

        layout.addWidget(output_group)

        # Format Options
        format_group = QGroupBox("Format Options")
        format_layout = QGridLayout(format_group)

        format_layout.addWidget(QLabel("Output Format:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(
            ["NML (Traktor)", "M3U (Basic)", "M3U8 (Extended)", "All Formats"]
        )
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo, 0, 1)

        # Format-specific options
        self.use_suffix_checkbox = QCheckBox("Add format suffix to filenames")
        self.use_suffix_checkbox.setToolTip(
            "Adds format suffix to filename for clarity (e.g. 'My Playlist_nml.nml')"
        )
        format_layout.addWidget(self.use_suffix_checkbox, 1, 0, 1, 2)

        layout.addWidget(format_group)

        # M3U Options (shown conditionally)
        self.m3u_group = QGroupBox("M3U/M3U8 Options")
        m3u_layout = QGridLayout(self.m3u_group)

        self.m3u_extended_checkbox = QCheckBox("Use extended format (with metadata)")
        self.m3u_extended_checkbox.setChecked(True)
        m3u_layout.addWidget(self.m3u_extended_checkbox, 0, 0, 1, 2)

        # Path type radio buttons
        m3u_layout.addWidget(QLabel("Path Type:"), 1, 0)

        path_type_layout = QHBoxLayout()
        self.relative_paths_radio = QRadioButton("Relative paths")
        self.absolute_paths_radio = QRadioButton("Absolute paths")
        self.relative_paths_radio.setChecked(True)  # Default to relative

        path_type_layout.addWidget(self.relative_paths_radio)
        path_type_layout.addWidget(self.absolute_paths_radio)
        path_type_layout.addStretch()

        m3u_layout.addLayout(path_type_layout, 1, 1)

        layout.addWidget(self.m3u_group)

        # NML Options (shown conditionally)
        # self.nml_group = QGroupBox("NML (Traktor) Options")
        # nml_layout = QVBoxLayout(self.nml_group)

        # Add placeholder text since cue points and loops aren't implemented yet
        # nml_info = QLabel("Basic NML export (cue points and loops coming soon)")
        # nml_info.setStyleSheet("color: #666; font-style: italic;")
        # nml_layout.addWidget(nml_info)

        # layout.addWidget(self.nml_group)

        # Conversion Button
        self.convert_button = QPushButton("Convert Selected Playlists")
        self.convert_button.setEnabled(False)
        self.convert_button.setMinimumHeight(40)
        self.convert_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """
        )
        self.convert_button.clicked.connect(self._start_conversion)
        layout.addWidget(self.convert_button)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

        # Initial format change to set visibility
        self._on_format_changed()

        return tab

    def _create_output_tab(self) -> QWidget:
        """Create the output and logs tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Options
        options_layout = QHBoxLayout()
        self.verbose_checkbox = QCheckBox("Verbose logging")
        self.clear_logs_button = QPushButton("Clear Logs")
        self.clear_logs_button.clicked.connect(self._clear_logs)

        options_layout.addWidget(self.verbose_checkbox)
        options_layout.addStretch()
        options_layout.addWidget(self.clear_logs_button)
        layout.addLayout(options_layout)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier", 9))
        self.log_output.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555;
            }
        """
        )
        layout.addWidget(self.log_output)

        return tab

    def _setup_status_bar(self):
        """Setup the status bar."""
        sb = self.statusBar()
        sb.showMessage("Ready - Please connect a USB drive with Rekordbox data")

        # Add current application version (from pyproject.toml) as a permanent right-side label
        version = __version__
        if version and version != "0.0.0":
            version_label = QLabel(f"v{version}")
            version_label.setStyleSheet("color: #888;")
            version_label.setToolTip("Application version")
            sb.addPermanentWidget(version_label)

    def _start_usb_detection(self):
        """Start USB drive detection in background."""
        self._log_message("[USB Detection] Starting USB detection worker...")

        # Direct USB detection without threads
        self._log_message("[USB Detection] Scanning for USB drives...")
        drives = self._detect_usb_drives_direct()
        self._on_usb_drives_found(drives)

    def _on_usb_drives_found(self, drives: List[USBDriveInfo]):
        """Handle USB drives detection results."""
        self._log_message(f"[USB Detection] Found {len(drives)} USB drives")
        for drive in drives:
            self._log_message(
                f"[USB Detection]   - {drive.label}: {drive.path} (Rekordbox: {drive.has_rekordbox})"
            )

        self.available_drives = drives

        if not drives:
            self.usb_label.setText("No USB drives detected")
            self.usb_label.setStyleSheet("color: #666; font-style: italic;")
            self.usb_drive_combo.clear()
            self.usb_drive_combo.setEnabled(False)
            self._clear_playlists()
            self._log_message("[USB Detection] No USB drives found")
            return

        # Find drives with Rekordbox data
        rekordbox_drives = [d for d in drives if d.has_rekordbox]
        other_drives = [d for d in drives if not d.has_rekordbox]

        self._log_message(f"[USB Detection] Rekordbox drives: {len(rekordbox_drives)}")
        self._log_message(f"[USB Detection] Other drives: {len(other_drives)}")

        # Update combo box
        self.usb_drive_combo.clear()
        self.usb_drive_combo.setEnabled(True)

        for drive in rekordbox_drives:
            size_gb = drive.size / (1024**3)
            free_gb = drive.free_space / (1024**3)
            label = f"✅ {drive.label} ({size_gb:.1f}GB) - Rekordbox"
            self.usb_drive_combo.addItem(label, drive)
            self._log_message(
                f"[USB Detection] Added Rekordbox drive to combo: {label}"
            )

        for drive in other_drives:
            size_gb = drive.size / (1024**3)
            free_gb = drive.free_space / (1024**3)
            label = f"❌ {drive.label} ({size_gb:.1f}GB) - No Rekordbox"
            self.usb_drive_combo.addItem(label, drive)
            self._log_message(
                f"[USB Detection] Added non-Rekordbox drive to combo: {label}"
            )

        if not rekordbox_drives:
            drive_info = (
                f"Found {len(drives)} USB drive(s), but no Rekordbox data detected"
            )
            self.usb_label.setText(drive_info)
            self.usb_label.setStyleSheet("color: #ff6600; font-weight: bold;")
            self._clear_playlists()
            self._log_message("[USB Detection] No drives with Rekordbox data found")
            return

        # Auto-select the first Rekordbox drive
        self.usb_drive_combo.setCurrentIndex(0)
        self._log_message(f"[USB Detection] Auto-selecting first Rekordbox drive")
        self._on_usb_drive_selected(self.usb_drive_combo.currentText())

    def _refresh_usb_drives(self):
        """Manually refresh USB drive detection."""
        self.usb_label.setText("Refreshing...")
        self._log_message("[USB Detection] Manual refresh triggered")

        # Instead of using a background thread, do a direct scan
        # This avoids threading issues
        try:
            from .parser import RekordboxParser  # Import here to avoid circular imports

            drives = self._detect_usb_drives_direct()
            self._on_usb_drives_found(drives)
        except Exception as e:
            self._log_message(f"[USB Detection] Error during manual scan: {e}")
            self.usb_label.setText("Error scanning drives")
            self.usb_label.setStyleSheet("color: red; font-weight: bold;")

    def _detect_usb_drives_direct(self) -> List[USBDriveInfo]:
        """Direct USB drive detection without threading."""
        drives = []
        partitions = psutil.disk_partitions()

        self._log_message(
            f"[USB Detection] Scanning {len(partitions)} partitions directly..."
        )

        for partition in partitions:
            # Only check drives that look like USB drives
            if "removable" in partition.opts or self._is_usb_drive_simple(
                partition.device, partition.mountpoint, partition.fstype
            ):
                try:
                    path = Path(partition.mountpoint)
                    usage = psutil.disk_usage(partition.mountpoint)

                    # Check if it has Rekordbox database
                    rekordbox_path = path / "PIONEER" / "rekordbox" / "export.pdb"
                    has_rekordbox = rekordbox_path.exists()

                    drives.append(
                        USBDriveInfo(
                            path=path,
                            label=partition.mountpoint,
                            size=usage.total,
                            free_space=usage.free,
                            has_rekordbox=has_rekordbox,
                        )
                    )

                    self._log_message(
                        f"[USB Detection] Found USB drive: {partition.device} -> {partition.mountpoint} (Rekordbox: {has_rekordbox})"
                    )

                except (PermissionError, OSError) as e:
                    self._log_message(
                        f"[USB Detection] Error accessing {partition.device}: {e}"
                    )
                    continue

        return drives

    def _is_usb_drive_simple(
        self, device: str, mountpoint: str = None, filesystem: str = None
    ) -> bool:
        """Simple USB drive detection without verbose logging."""
        # Check mount point first (most reliable)
        if mountpoint:
            if mountpoint.startswith("/Volumes/"):  # macOS external drives
                return True
            elif mountpoint.startswith("/media/") or mountpoint.startswith(
                "/mnt/"
            ):  # Linux
                return True
            elif (
                len(mountpoint) == 3 and mountpoint[1:] == ":\\"
            ):  # Windows drive letters
                return True

        # Check filesystem types commonly used by USB drives
        if filesystem:
            usb_filesystems = ["msdos", "exfat", "vfat", "ntfs", "fat32", "fat"]
            if filesystem.lower() in usb_filesystems:
                return True

        # Check device path patterns
        if device:
            if "usb" in device.lower():
                return True
            elif (
                "/dev/disk" in device
                and mountpoint
                and mountpoint.startswith("/Volumes/")
            ):
                return True

        return False

    def _on_usb_drive_selected(self, selection_text: str):
        """Handle USB drive selection from combo box."""
        self._log_message(f"[USB Selection] Drive selected: {selection_text}")

        if not selection_text:
            self._log_message("[USB Selection] Empty selection text")
            return

        # Get the currently selected drive
        current_index = self.usb_drive_combo.currentIndex()
        if current_index < 0:
            self._log_message(f"[USB Selection] Invalid index: {current_index}")
            return

        selected_drive = self.usb_drive_combo.itemData(current_index)
        if not selected_drive or not isinstance(selected_drive, USBDriveInfo):
            self._log_message(f"[USB Selection] Invalid drive data: {selected_drive}")
            return

        self._log_message(f"[USB Selection] Selected drive path: {selected_drive.path}")
        self._log_message(
            f"[USB Selection] Has Rekordbox: {selected_drive.has_rekordbox}"
        )

        # Check if drive has Rekordbox data
        if not selected_drive.has_rekordbox:
            message = f"Selected drive has no Rekordbox data: {selected_drive.label}"
            self.usb_label.setText(message)
            self.usb_label.setStyleSheet("color: #ff6600; font-weight: bold;")
            self._clear_playlists()
            self._log_message(f"[USB Selection] {message}")
            return

        # Update status and parse playlists
        size_gb = selected_drive.size / (1024**3)
        free_gb = selected_drive.free_space / (1024**3)
        # Use paragraph tags with margins for better line spacing
        drive_info = (
            f"<p style='margin: 0 0 5px 0;'>💽 {selected_drive.label} ({size_gb:.1f}GB, {free_gb:.1f}GB free)</p>"
            f"<p style='margin: 0;'>🎛️ Rekordbox playlists detected!</p>"
        )
        self.usb_label.setText(drive_info)
        self.usb_label.setTextFormat(Qt.RichText)
        self.usb_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

        # Parse playlists if this is a different drive
        if self.current_usb_path != selected_drive.path:
            self._log_message(
                f"[USB Selection] New drive detected, parsing playlists..."
            )
            self.current_usb_path = selected_drive.path
            self._parse_playlists()
        elif not self.playlist_tree:
            # Same drive but no playlists loaded, force refresh
            self._log_message(
                f"[USB Selection] Same drive but no playlists, refreshing..."
            )
            self._parse_playlists()
        else:
            self._log_message(
                f"[USB Selection] Same drive and playlists already loaded"
            )

    def _parse_playlists(self):
        """Parse playlists from the current USB drive synchronously."""
        if not self.current_usb_path:
            return

        self._clear_playlists()
        self._log_message("Starting playlist parsing...")

        try:
            # Parse synchronously without threading
            self._log_message("Initializing parser...")

            # Build the path to the Rekordbox database
            rekordbox_pdb_path = (
                self.current_usb_path / "PIONEER" / "rekordbox" / "export.pdb"
            )
            self._log_message(f"Looking for database at: {rekordbox_pdb_path}")

            if not rekordbox_pdb_path.exists():
                raise FileNotFoundError(
                    f"Rekordbox database not found at {rekordbox_pdb_path}"
                )

            parser = RekordboxParser(rekordbox_pdb_path)

            self._log_message("Loading Rekordbox database...")
            if not parser.parse():
                raise RuntimeError("Failed to parse the Rekordbox database")

            # Store parser for later use in enhancement
            self.current_parser = parser

            self._log_message("Extracting playlists...")
            playlist_tree = parser.get_playlists(self.current_usb_path)

            self._log_message("Parsing complete!")
            self._on_playlists_parsed(playlist_tree)

        except Exception as e:
            error_message = f"Failed to parse playlists: {str(e)}"
            self._on_parsing_error(error_message)

    def _on_playlists_parsed(self, playlist_tree: PlaylistTree):
        """Handle successful playlist parsing."""
        self.playlist_tree = playlist_tree
        self._populate_playlist_tree()
        self._update_conversion_button_state()
        self._log_message(
            f"Successfully loaded {len(playlist_tree.all_playlists)} playlists!"
        )
        self.statusBar().showMessage(
            f"Ready - {len(playlist_tree.all_playlists)} playlists loaded"
        )

    def _on_parsing_error(self, error_message: str):
        """Handle playlist parsing errors."""
        self._log_message(f"Error: {error_message}")
        QMessageBox.critical(self, "Parsing Error", error_message)
        self.statusBar().showMessage("Error - Failed to load playlists")

    def _populate_playlist_tree(self):
        """Populate the playlist tree widget."""
        self.playlist_tree_widget.clear()
        if not self.playlist_tree:
            return

        # Add all playlists (flatten hierarchy for now)
        for order, playlist in enumerate(self.playlist_tree.all_playlists.values()):
            if not playlist.is_folder:  # Only show actual playlists, not folders
                track_count = len(playlist.tracks)
                order_number = order + 1  # Original order from Rekordbox (1-based)

                # Create item with only the playlist name (column 0)
                item = QTreeWidgetItem([playlist.name])

                # Set the display data for all columns properly
                # Column 0: Playlist name (string) - already set in constructor
                # Column 1: Track count - set as integer for proper sorting
                item.setData(1, Qt.DisplayRole, track_count)
                # Column 2: Order - set as integer for proper sorting
                item.setData(2, Qt.DisplayRole, order_number)

                item.setCheckState(0, Qt.Unchecked)
                item.setData(0, Qt.UserRole, playlist)
                self.playlist_tree_widget.addTopLevelItem(item)

        # Enable sorting - this will now work properly with numeric data
        self.playlist_tree_widget.setSortingEnabled(True)
        # Sort by original order by default (column 2)
        self.playlist_tree_widget.sortByColumn(2, Qt.AscendingOrder)

        self.select_all_button.setEnabled(True)
        self.select_none_button.setEnabled(True)

    def _clear_playlists(self):
        """Clear the playlist tree."""
        self.playlist_tree_widget.clear()
        self.selected_playlists.clear()
        self.playlist_tree = None
        self.select_all_button.setEnabled(False)
        self.select_none_button.setEnabled(False)
        self._update_conversion_button_state()

        # Update status message
        if not self.available_drives:
            self.statusBar().showMessage(
                "Ready - Please connect a USB drive with Rekordbox data"
            )
        elif not any(d.has_rekordbox for d in self.available_drives):
            self.statusBar().showMessage(
                "Ready - No Rekordbox data found on connected drives"
            )
        else:
            self.statusBar().showMessage("Ready - Select a drive with Rekordbox data")

    def _on_playlist_selection_changed(self, item: QTreeWidgetItem, column: int):
        """Handle playlist selection changes."""
        playlist = item.data(0, Qt.UserRole)
        if playlist:
            if item.checkState(0) == Qt.Checked:
                self.selected_playlists[playlist.name] = playlist
            else:
                self.selected_playlists.pop(playlist.name, None)

        self._update_conversion_button_state()

    def _select_all_playlists(self):
        """Select all playlists."""
        for i in range(self.playlist_tree_widget.topLevelItemCount()):
            item = self.playlist_tree_widget.topLevelItem(i)
            item.setCheckState(0, Qt.Checked)

    def _select_no_playlists(self):
        """Deselect all playlists."""
        for i in range(self.playlist_tree_widget.topLevelItemCount()):
            item = self.playlist_tree_widget.topLevelItem(i)
            item.setCheckState(0, Qt.Unchecked)

    def _on_format_changed(self):
        """Handle format selection changes."""
        format_text = self.format_combo.currentText()

        # Show/hide format-specific options
        show_m3u = "M3U" in format_text or "All" in format_text
        show_nml = "NML" in format_text or "All" in format_text

        self.m3u_group.setVisible(show_m3u)
        # self.nml_group.setVisible(show_nml) # comentado porque aun no hay opciones

    def _browse_output_directory(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", str(Path.home())
        )
        if directory:
            self.output_dir_label.setText(directory)
            self.output_dir_label.setStyleSheet("color: #666; font-style: normal;")
            self._update_conversion_button_state()

    def _update_conversion_button_state(self):
        """Update the conversion button enabled state."""
        has_playlists = len(self.selected_playlists) > 0
        has_output_dir = self.output_dir_label.text() != "No directory selected"

        self.convert_button.setEnabled(has_playlists and has_output_dir)

        if has_playlists and has_output_dir:
            count = len(self.selected_playlists)
            self.convert_button.setText(
                f"Convert {count} Selected Playlist{'s' if count != 1 else ''}"
            )
        else:
            self.convert_button.setText("Convert Selected Playlists")

    def _start_conversion(self):
        """Start the conversion process."""
        if (
            not self.selected_playlists
            or self.output_dir_label.text() == "No directory selected"
        ):
            return

        # Create conversion config
        config = self._create_conversion_config()
        output_dir = Path(self.output_dir_label.text())
        playlists = list(self.selected_playlists.values())

        # Disable UI during conversion
        self.convert_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Start conversion worker
        self.conversion_worker = ConversionWorker(
            playlists, config, output_dir, self.current_usb_path, self.current_parser
        )
        self.conversion_worker.conversion_progress.connect(self._on_conversion_progress)
        self.conversion_worker.conversion_complete.connect(self._on_conversion_complete)
        self.conversion_worker.start()

    def _create_conversion_config(self) -> ConversionConfig:
        """Create conversion configuration from UI settings."""
        format_map = {
            "NML (Traktor)": "nml",
            "M3U (Basic)": "m3u",
            "M3U8 (Extended)": "m3u8",
            "All Formats": "all",
        }

        return ConversionConfig(
            relative_paths=self.relative_paths_radio.isChecked(),
            include_cue_points=False,  # Not implemented yet
            include_loops=False,  # Not implemented yet
            output_format=format_map[self.format_combo.currentText()],
            use_format_suffix=self.use_suffix_checkbox.isChecked(),
            m3u_extended=self.m3u_extended_checkbox.isChecked(),
            m3u_absolute_paths=self.absolute_paths_radio.isChecked(),
        )

    def _on_conversion_progress(self, message: str, progress: int):
        """Handle conversion progress updates."""
        self.progress_bar.setValue(progress)
        self._log_message(message)
        self.statusBar().showMessage(message)

    def _on_conversion_complete(self, results: List[ConversionResult]):
        """Handle conversion completion."""
        # Re-enable UI
        self.convert_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._update_conversion_button_state()

        # Show results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        self._log_message(f"\n=== Conversion Complete ===")
        self._log_message(f"✅ Successful: {len(successful)}")
        self._log_message(f"❌ Failed: {len(failed)}")

        for result in successful:
            self._log_message(f"✅ {result.playlist_name} -> {result.output_file}")

        for result in failed:
            self._log_message(f"❌ {result.playlist_name}: {result.error_message}")

        # Show summary dialog
        if failed:
            QMessageBox.warning(
                self,
                "Conversion Complete",
                f"Conversion completed with {len(failed)} errors.\nCheck the logs for details.",
            )
        else:
            QMessageBox.information(
                self,
                "Conversion Complete",
                f"Successfully converted {len(successful)} playlist(s)!",
            )

        self.statusBar().showMessage(
            f"Conversion complete - {len(successful)} successful, {len(failed)} failed"
        )

    def _log_message(self, message: str):
        """Add a message to the log output."""
        self.log_output.append(message)
        self.log_output.ensureCursorVisible()

        # Also log to Python logger if verbose mode
        if self.verbose_checkbox.isChecked():
            self.logger.info(message)

    def _clear_logs(self):
        """Clear the log output."""
        self.log_output.clear()

    def closeEvent(self, event):
        """Handle application close."""
        print("Application closing, stopping background workers...")

        # No USB worker or parsing worker to stop anymore - using direct method calls

        # Stop conversion worker only
        if self.conversion_worker and self.conversion_worker.isRunning():
            print("Stopping conversion worker...")
            self.conversion_worker.terminate()
            self.conversion_worker.wait(3000)
            self.conversion_worker = None

        print("All workers stopped, accepting close event")
        event.accept()


def main():
    """Main entry point for the GUI application."""
    # Ensure we have a proper display environment
    if sys.platform.startswith("darwin"):  # macOS
        import os

        os.environ.setdefault("QT_MAC_WANTS_LAYER", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("Universal DJ USB Playlist Converter")
    if __version__ and __version__ != "0.0.0":
        app.setApplicationVersion(__version__)

    # Ensure app doesn't quit when last window closes in some cases
    app.setQuitOnLastWindowClosed(True)

    # Signal handler for clean shutdown - Qt style
    def signal_handler(sig, frame):
        print("\n[App] Received interrupt signal, shutting down...")
        app.quit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Enable Ctrl+C handling in Qt (override previous handler)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        window = MainWindow()

        # Show the window first
        window.show()

        # Process events to ensure window is displayed
        app.processEvents()

        # Force the window to show and raise to front
        window.raise_()
        window.activateWindow()

        # On macOS, ensure the app comes to front
        if sys.platform.startswith("darwin"):
            window.raise_()

        print("[App] GUI window should now be visible")

        # Run the application
        result = app.exec()

        # Clean up
        print("[App] App finished, cleaning up...")

        return result

    except Exception as e:
        print(f"[App] Error starting application: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
