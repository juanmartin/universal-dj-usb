# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['udj_cli.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/universal_dj_usb', 'universal_dj_usb')],
    hiddenimports=['universal_dj_usb', 'universal_dj_usb.models', 'universal_dj_usb.parser', 'universal_dj_usb.metadata_extractor', 'universal_dj_usb.generators', 'universal_dj_usb.generators.base', 'universal_dj_usb.generators.nml', 'universal_dj_usb.generators.m3u', 'universal_dj_usb.generators.m3u8', 'universal_dj_usb.kaitai.rekordbox_pdb', 'click', 'rich.console', 'rich.table', 'rich.progress', 'rich.panel', 'rich.logging', 'lxml.etree', 'lxml._elementpath', 'kaitaistruct', 'mutagen.mp3', 'mutagen.mp4', 'mutagen.flac', 'mutagen.oggvorbis', 'mutagen.id3', 'psutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'IPython', 'jupyter'],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('O', None, 'OPTION'), ('O', None, 'OPTION')],
    name='udj',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
