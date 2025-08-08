#!/usr/bin/env python3
# filepath: /Users/juanmartin/REPOS/REPROPIOS/universal-dj-usb/scripts/compare_nml_files.py

import sys
from pathlib import Path


def analyze_file(filepath: Path) -> dict:
    """Analyze file for encoding and formatting issues."""
    with open(filepath, "rb") as f:
        raw_bytes = f.read()

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    analysis = {
        "file_size": len(raw_bytes),
        "has_bom": raw_bytes.startswith(b"\xef\xbb\xbf"),
        "line_ending_type": "unknown",
        "first_bytes": raw_bytes[:20].hex(),
        "permissions": oct(filepath.stat().st_mode)[-3:],
    }

    # Detect line endings
    if "\r\n" in content:
        analysis["line_ending_type"] = "CRLF (Windows)"
    elif "\n" in content:
        analysis["line_ending_type"] = "LF (Unix/macOS)"
    elif "\r" in content:
        analysis["line_ending_type"] = "CR (Old Mac)"

    return analysis


def main():
    if len(sys.argv) != 3:
        print("Usage: python compare_nml_files.py file1.nml file2.nml")
        sys.exit(1)

    file1 = Path(sys.argv[1])
    file2 = Path(sys.argv[2])

    print("=== NML File Analysis ===\n")

    analysis1 = analyze_file(file1)
    analysis2 = analyze_file(file2)

    print(f"File 1: {file1}")
    for key, value in analysis1.items():
        print(f"  {key}: {value}")

    print(f"\nFile 2: {file2}")
    for key, value in analysis2.items():
        print(f"  {key}: {value}")

    print("\n=== Differences ===")
    differences = []
    for key in analysis1:
        if analysis1[key] != analysis2[key]:
            differences.append(f"{key}: {analysis1[key]} vs {analysis2[key]}")

    if differences:
        for diff in differences:
            print(f"  ❌ {diff}")
    else:
        print("  ✅ No encoding/formatting differences found")


if __name__ == "__main__":
    main()
