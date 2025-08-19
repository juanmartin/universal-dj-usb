# Application Assets

This directory contains assets for the Universal DJ USB application.

## Icons

To add application icons, place them here:

- `app_icon.icns` - macOS application icon (512x512 recommended)
- `app_icon.ico` - Windows application icon (256x256 with multiple sizes)
- `app_icon.png` - Linux/fallback icon (512x512 recommended)
- `app_icon@2x.png` - High-DPI version for Retina displays

## Icon Requirements

### macOS (.icns)

- Use Icon Composer or iconutil to create from PNG sources
- Include multiple sizes: 16x16, 32x32, 128x128, 256x256, 512x512
- Use `iconutil -c icns app_icon.iconset` to create from iconset folder

### Windows (.ico)

- Include multiple sizes in single file: 16x16, 32x32, 48x48, 256x256
- Use tools like ImageMagick: `convert app_icon.png -resize 256x256 app_icon.ico`

### Linux (.png)

- Standard PNG format
- 512x512 recommended for best compatibility
- Fallback for other platforms

## Usage in Code

```python
from universal_dj_usb.assets import get_app_icon

icon_path = get_app_icon()
if icon_path:
    app.setWindowIcon(QIcon(str(icon_path)))
```
