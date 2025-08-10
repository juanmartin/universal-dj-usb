#!/usr/bin/env python3
"""Debug script to inspect PDB structure."""

from pathlib import Path
import sys
sys.path.insert(0, 'src')

from universal_dj_usb.parser import RekordboxParser

def debug_pdb_structure():
    parser = RekordboxParser(Path('/Volumes/JMSM_SANDIS/PIONEER/rekordbox/export.pdb'))
    parser.parse()
    
    print("=== TRACKS TABLE ===")
    # Find tracks table and inspect first track
    for table in parser.pdb_data.tables:
        if table.type.name == 'tracks':
            page = table.first_page
            if page and page.body.is_data_page:
                for row_group in page.body.row_groups:
                    for row_ref in row_group.rows:
                        if row_ref.present and row_ref.body:
                            track_row = row_ref.body
                            print('Track attributes:', [attr for attr in dir(track_row) if not attr.startswith('_')])
                            print('Track ID:', getattr(track_row, 'id', 'NO ID'))
                            
                            # Try different potential attribute names
                            for attr in ['title', 'artist', 'album', 'file_path', 'filename']:
                                if hasattr(track_row, attr):
                                    val = getattr(track_row, attr)
                                    if val and hasattr(val, 'body') and val.body:
                                        print(f'{attr}:', val.body.text)
                                    else:
                                        print(f'{attr}:', val)
                            
                            # Try ID fields
                            for attr in ['artist_id', 'album_id', 'genre_id']:
                                if hasattr(track_row, attr):
                                    print(f'{attr}:', getattr(track_row, attr))
                            
                            break
                    break
                break
            break
    
    print("\n=== PLAYLIST ENTRIES TABLE ===")
    # Find playlist entries table
    for table in parser.pdb_data.tables:
        if table.type.name == 'playlist_entries':
            page = table.first_page
            if page and page.body.is_data_page:
                for row_group in page.body.row_groups:
                    for row_ref in row_group.rows[:1]:  # Just first one
                        if row_ref.present and row_ref.body:
                            entry_row = row_ref.body
                            print('Entry attributes:', [attr for attr in dir(entry_row) if not attr.startswith('_')])
                            break
                    break
                break
            break

if __name__ == "__main__":
    debug_pdb_structure()
