"""Graphical user interface for the Universal DJ USB playlist converter."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import queue
import time

from .converter import RekordboxToTraktorConverter
from .models import ConversionConfig, ConversionResult
from .utils import get_platform_specific_paths, load_config

logger = logging.getLogger(__name__)


class ConversionWorker(threading.Thread):
    """Worker thread for playlist conversion to avoid blocking the GUI."""

    def __init__(
        self,
        converter: RekordboxToTraktorConverter,
        usb_path: Path,
        output_path: Path,
        selected_playlists: Optional[List[str]],
        result_queue: queue.Queue,
    ):
        super().__init__(daemon=True)
        self.converter = converter
        self.usb_path = usb_path
        self.output_path = output_path
        self.selected_playlists = selected_playlists
        self.result_queue = result_queue
        self._stop_event = threading.Event()

    def run(self) -> None:
        """Run the conversion in a separate thread."""
        try:
            results = self.converter.convert_all_playlists(
                self.usb_path, self.output_path, self.selected_playlists
            )

            if not self._stop_event.is_set():
                self.result_queue.put(("success", results))

        except Exception as e:
            if not self._stop_event.is_set():
                self.result_queue.put(("error", str(e)))

    def stop(self) -> None:
        """Stop the conversion thread."""
        self._stop_event.set()


class PlaylistSelectorDialog:
    """Dialog for selecting specific playlists to convert."""

    def __init__(self, parent: tk.Tk, playlists: List[str]):
        self.parent = parent
        self.playlists = playlists
        self.selected_playlists = []
        self.dialog = None
        self.result = None

        self._create_dialog()

    def _create_dialog(self) -> None:
        """Create the playlist selection dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Select Playlists to Convert")
        self.dialog.geometry("500x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")

        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Instructions
        ttk.Label(
            main_frame,
            text="Select the playlists you want to convert:",
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # Playlist listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )

        self.listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=15)
        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.listbox.yview
        )
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Add playlists to listbox
        for playlist in self.playlists:
            self.listbox.insert(tk.END, playlist)

        # Select all button
        ttk.Button(main_frame, text="Select All", command=self._select_all).grid(
            row=2, column=0, sticky=tk.W, pady=(0, 10)
        )

        # Clear selection button
        ttk.Button(
            main_frame, text="Clear Selection", command=self._clear_selection
        ).grid(row=2, column=1, sticky=tk.E, pady=(0, 10))

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))

        ttk.Button(
            button_frame, text="Convert Selected", command=self._convert_selected
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(button_frame, text="Convert All", command=self._convert_all).pack(
            side=tk.RIGHT
        )

        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.LEFT)

        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)

    def _select_all(self) -> None:
        """Select all playlists."""
        self.listbox.select_set(0, tk.END)

    def _clear_selection(self) -> None:
        """Clear all selections."""
        self.listbox.selection_clear(0, tk.END)

    def _convert_selected(self) -> None:
        """Convert only selected playlists."""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning(
                "No Selection", "Please select at least one playlist."
            )
            return

        self.selected_playlists = [self.playlists[i] for i in selected_indices]
        self.result = "selected"
        self.dialog.destroy()

    def _convert_all(self) -> None:
        """Convert all playlists."""
        self.selected_playlists = None  # None means all playlists
        self.result = "all"
        self.dialog.destroy()

    def _cancel(self) -> None:
        """Cancel the dialog."""
        self.result = "cancel"
        self.dialog.destroy()

    def show(self) -> tuple:
        """Show the dialog and return the result."""
        self.parent.wait_window(self.dialog)
        return self.result, self.selected_playlists


class UniversalDJUSBGUI:
    """Main GUI application for the Universal DJ USB converter."""

    def __init__(self):
        self.root = tk.Tk()
        self.converter = None
        self.conversion_worker = None
        self.result_queue = queue.Queue()

        # Paths
        self.usb_path = None
        self.output_path = None

        # GUI elements
        self.usb_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_bar = None

        self._setup_gui()
        self._load_config()
        self._start_result_checker()

    def _setup_gui(self) -> None:
        """Set up the main GUI."""
        self.root.title("Universal DJ USB Playlist Converter")
        self.root.geometry("700x500")

        # Make window resizable
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Create main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10
        )

        # Conversion tab
        self.conversion_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.conversion_frame, text="Convert Playlists")

        # Settings tab
        self.settings_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.settings_frame, text="Settings")

        self._setup_conversion_tab()
        self._setup_settings_tab()

    def _setup_conversion_tab(self) -> None:
        """Set up the main conversion tab."""
        # Title
        title_label = ttk.Label(
            self.conversion_frame,
            text="Universal DJ USB Playlist Converter",
            font=("TkDefaultFont", 16, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # USB Drive Selection
        usb_frame = ttk.LabelFrame(
            self.conversion_frame, text="USB Drive", padding="10"
        )
        usb_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        usb_frame.columnconfigure(1, weight=1)

        ttk.Label(usb_frame, text="USB Drive Path:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5)
        )
        usb_entry = ttk.Entry(
            usb_frame, textvariable=self.usb_path_var, state="readonly"
        )
        usb_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(usb_frame, text="Browse", command=self._browse_usb_drive).grid(
            row=0, column=2
        )

        ttk.Button(usb_frame, text="Auto-Detect", command=self._auto_detect_usb).grid(
            row=0, column=3, padx=(5, 0)
        )

        # Output Directory Selection
        output_frame = ttk.LabelFrame(
            self.conversion_frame, text="Output Directory", padding="10"
        )
        output_frame.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        output_frame.columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="Output Directory:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5)
        )
        output_entry = ttk.Entry(
            output_frame, textvariable=self.output_path_var, state="readonly"
        )
        output_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(
            output_frame, text="Browse", command=self._browse_output_directory
        ).grid(row=0, column=2)

        # Conversion Options
        options_frame = ttk.LabelFrame(
            self.conversion_frame, text="Options", padding="10"
        )
        options_frame.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        self.convert_all_var = tk.BooleanVar(value=True)
        ttk.Radiobutton(
            options_frame,
            text="Convert all playlists",
            variable=self.convert_all_var,
            value=True,
        ).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        ttk.Radiobutton(
            options_frame,
            text="Select specific playlists",
            variable=self.convert_all_var,
            value=False,
        ).grid(row=1, column=0, sticky=tk.W)

        # Action Buttons
        button_frame = ttk.Frame(self.conversion_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0))

        self.list_button = ttk.Button(
            button_frame, text="List Playlists", command=self._list_playlists
        )
        self.list_button.pack(side=tk.LEFT, padx=(0, 5))

        self.convert_button = ttk.Button(
            button_frame, text="Start Conversion", command=self._start_conversion
        )
        self.convert_button.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_button = ttk.Button(
            button_frame, text="Stop", command=self._stop_conversion, state="disabled"
        )
        self.stop_button.pack(side=tk.LEFT)

        # Progress Section
        progress_frame = ttk.LabelFrame(
            self.conversion_frame, text="Progress", padding="10"
        )
        progress_frame.grid(
            row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0)
        )
        progress_frame.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(progress_frame, mode="indeterminate")
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        progress_label.grid(row=1, column=0, sticky=tk.W)

        # Configure grid weights
        self.conversion_frame.columnconfigure(0, weight=1)

    def _setup_settings_tab(self) -> None:
        """Set up the settings tab."""
        # File Options
        file_frame = ttk.LabelFrame(
            self.settings_frame, text="File Options", padding="10"
        )
        file_frame.grid(
            row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        self.relative_paths_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            file_frame, text="Use relative file paths", variable=self.relative_paths_var
        ).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.preserve_structure_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            file_frame,
            text="Preserve folder structure",
            variable=self.preserve_structure_var,
        ).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))

        # Content Options
        content_frame = ttk.LabelFrame(
            self.settings_frame, text="Content Options", padding="10"
        )
        content_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        self.include_cues_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            content_frame, text="Include cue points", variable=self.include_cues_var
        ).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.include_loops_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            content_frame, text="Include loops", variable=self.include_loops_var
        ).grid(row=1, column=0, sticky=tk.W)

        # File Naming
        naming_frame = ttk.LabelFrame(
            self.settings_frame, text="File Naming", padding="10"
        )
        naming_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        self.naming_var = tk.StringVar(value="playlist_name")
        ttk.Radiobutton(
            naming_frame,
            text="Use playlist name",
            variable=self.naming_var,
            value="playlist_name",
        ).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        ttk.Radiobutton(
            naming_frame,
            text="Use sequential numbering",
            variable=self.naming_var,
            value="sequential",
        ).grid(row=1, column=0, sticky=tk.W)

        # Configure grid weights
        self.settings_frame.columnconfigure(0, weight=1)

    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            paths = get_platform_specific_paths()
            config_path = paths["config"] / "config.toml"
            config_data = load_config(config_path)

            if "conversion" in config_data:
                conv_config = config_data["conversion"]
                self.relative_paths_var.set(conv_config.get("relative_paths", True))
                self.preserve_structure_var.set(
                    conv_config.get("preserve_folder_structure", True)
                )
                self.include_cues_var.set(conv_config.get("include_cue_points", True))
                self.include_loops_var.set(conv_config.get("include_loops", True))
                self.naming_var.set(conv_config.get("file_naming", "playlist_name"))

        except Exception as e:
            logger.warning(f"Failed to load config: {e}")

    def _get_config(self) -> ConversionConfig:
        """Get current configuration from GUI."""
        return ConversionConfig(
            relative_paths=self.relative_paths_var.get(),
            preserve_folder_structure=self.preserve_structure_var.get(),
            include_cue_points=self.include_cues_var.get(),
            include_loops=self.include_loops_var.get(),
            file_naming=self.naming_var.get(),
        )

    def _browse_usb_drive(self) -> None:
        """Browse for USB drive."""
        directory = filedialog.askdirectory(title="Select USB Drive")
        if directory:
            self.usb_path = Path(directory)
            self.usb_path_var.set(str(self.usb_path))
            self._validate_usb_drive()

    def _auto_detect_usb(self) -> None:
        """Auto-detect USB drives."""
        self.progress_var.set("Detecting USB drives...")
        self.root.update()

        try:
            config = self._get_config()
            self.converter = RekordboxToTraktorConverter(config)
            drives = self.converter.detect_usb_drives()

            if not drives:
                messagebox.showinfo(
                    "No Drives Found", "No USB drives with Rekordbox exports found."
                )
                self.progress_var.set("Ready")
                return

            if len(drives) == 1:
                self.usb_path = drives[0]
                self.usb_path_var.set(str(self.usb_path))
                messagebox.showinfo(
                    "Drive Found", f"Found Rekordbox export at: {self.usb_path}"
                )
            else:
                # Let user choose from multiple drives
                drive_names = [str(drive) for drive in drives]
                choice = self._choose_from_list(
                    "Multiple Drives Found", "Select a USB drive:", drive_names
                )
                if choice is not None:
                    self.usb_path = drives[choice]
                    self.usb_path_var.set(str(self.usb_path))

            self.progress_var.set("Ready")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to detect USB drives: {e}")
            self.progress_var.set("Ready")

    def _browse_output_directory(self) -> None:
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_path = Path(directory)
            self.output_path_var.set(str(self.output_path))

    def _validate_usb_drive(self) -> None:
        """Validate the selected USB drive."""
        if not self.usb_path:
            return

        config = self._get_config()
        self.converter = RekordboxToTraktorConverter(config)

        if not self.converter.validate_usb_drive(self.usb_path):
            messagebox.showerror(
                "Invalid USB Drive",
                f"No valid Rekordbox export found at {self.usb_path}\n\n"
                f"Expected: {self.usb_path}/PIONEER/rekordbox/export.pdb",
            )
            return False

        return True

    def _list_playlists(self) -> None:
        """List playlists on the USB drive."""
        if not self._validate_inputs():
            return

        try:
            self.progress_var.set("Reading playlists...")
            self.root.update()

            playlists = self.converter.list_playlists(self.usb_path)

            if not playlists:
                messagebox.showinfo(
                    "No Playlists", "No playlists found on the USB drive."
                )
            else:
                playlist_text = "\n".join(f"• {name}" for name in playlists)
                messagebox.showinfo(
                    f"Playlists Found ({len(playlists)})",
                    f"Found the following playlists:\n\n{playlist_text}",
                )

            self.progress_var.set("Ready")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to list playlists: {e}")
            self.progress_var.set("Ready")

    def _start_conversion(self) -> None:
        """Start the playlist conversion."""
        if not self._validate_inputs():
            return

        try:
            selected_playlists = None

            if not self.convert_all_var.get():
                # Get available playlists and let user select
                self.progress_var.set("Reading playlists...")
                self.root.update()

                playlists = self.converter.list_playlists(self.usb_path)

                if not playlists:
                    messagebox.showinfo(
                        "No Playlists", "No playlists found on the USB drive."
                    )
                    self.progress_var.set("Ready")
                    return

                # Show playlist selection dialog
                dialog = PlaylistSelectorDialog(self.root, playlists)
                result, selected_playlists = dialog.show()

                if result == "cancel":
                    self.progress_var.set("Ready")
                    return
                elif result == "selected" and not selected_playlists:
                    messagebox.showwarning("No Selection", "No playlists selected.")
                    self.progress_var.set("Ready")
                    return

            # Start conversion in worker thread
            self.conversion_worker = ConversionWorker(
                self.converter,
                self.usb_path,
                self.output_path,
                selected_playlists,
                self.result_queue,
            )

            self.conversion_worker.start()

            # Update UI state
            self.convert_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.progress_bar.config(mode="indeterminate")
            self.progress_bar.start()
            self.progress_var.set("Converting playlists...")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start conversion: {e}")
            self.progress_var.set("Ready")

    def _stop_conversion(self) -> None:
        """Stop the conversion process."""
        if self.conversion_worker and self.conversion_worker.is_alive():
            self.conversion_worker.stop()

        self._reset_ui_state()
        self.progress_var.set("Conversion stopped")

    def _validate_inputs(self) -> bool:
        """Validate user inputs."""
        if not self.usb_path:
            messagebox.showerror("Error", "Please select a USB drive.")
            return False

        if not self.output_path:
            messagebox.showerror("Error", "Please select an output directory.")
            return False

        if not self._validate_usb_drive():
            return False

        return True

    def _reset_ui_state(self) -> None:
        """Reset UI to initial state."""
        self.convert_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate")

    def _start_result_checker(self) -> None:
        """Start checking for conversion results."""
        self._check_conversion_results()

    def _check_conversion_results(self) -> None:
        """Check for conversion results from worker thread."""
        try:
            while True:
                result_type, result_data = self.result_queue.get_nowait()

                self._reset_ui_state()

                if result_type == "success":
                    self._show_conversion_results(result_data)
                elif result_type == "error":
                    messagebox.showerror(
                        "Conversion Error", f"Conversion failed: {result_data}"
                    )
                    self.progress_var.set("Conversion failed")

        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self._check_conversion_results)

    def _show_conversion_results(self, results: List[ConversionResult]) -> None:
        """Show conversion results to user."""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if successful and not failed:
            # All successful
            messagebox.showinfo(
                "Conversion Complete",
                f"Successfully converted {len(successful)} playlists to {self.output_path}",
            )
        elif successful and failed:
            # Mixed results
            messagebox.showwarning(
                "Conversion Complete with Errors",
                f"Successfully converted {len(successful)} playlists.\n"
                f"Failed to convert {len(failed)} playlists.\n\n"
                f"Output directory: {self.output_path}",
            )
        else:
            # All failed
            messagebox.showerror(
                "Conversion Failed", f"Failed to convert all {len(failed)} playlists."
            )

        self.progress_var.set(f"Converted {len(successful)}/{len(results)} playlists")

    def _choose_from_list(
        self, title: str, message: str, choices: List[str]
    ) -> Optional[int]:
        """Show a dialog to choose from a list of options."""
        # Simple implementation - could be improved with a custom dialog
        choice_text = "\n".join(f"{i+1}. {choice}" for i, choice in enumerate(choices))
        full_message = (
            f"{message}\n\n{choice_text}\n\nEnter the number (1-{len(choices)}):"
        )

        while True:
            result = tk.simpledialog.askstring(title, full_message)
            if result is None:  # User cancelled
                return None

            try:
                choice_num = int(result) - 1
                if 0 <= choice_num < len(choices):
                    return choice_num
                else:
                    messagebox.showerror(
                        "Invalid Choice",
                        f"Please enter a number between 1 and {len(choices)}",
                    )
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number")

    def run(self) -> None:
        """Run the GUI application."""
        try:
            # Set default output path
            self.output_path = Path.home() / "Desktop" / "converted_playlists"
            self.output_path_var.set(str(self.output_path))

            self.root.mainloop()
        except Exception as e:
            logger.error(f"GUI error: {e}")
            messagebox.showerror(
                "Application Error", f"An unexpected error occurred: {e}"
            )


def main() -> None:
    """Main entry point for the GUI application."""
    import tkinter.simpledialog

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        app = UniversalDJUSBGUI()
        app.run()
    except Exception as e:
        logger.error(f"Failed to start GUI: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
