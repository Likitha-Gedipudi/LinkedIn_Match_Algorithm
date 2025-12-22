# Extension Icon Generation

You need to create 3 icon files for the Chrome extension:

- `icon16.png` (16x16 pixels)
- `icon48.png` (48x48 pixels)  
- `icon128.png` (128x128 pixels)

## Quick Generation Options

### Option 1: Using Online Tool

1. Visit https://www.favicon-generator.org/
2. Upload your logo/image
3. Download the generated icons
4. Rename and place in this `icons/` folder

### Option 2: Using ImageMagick (Command Line)

```bash
# Install ImageMagick first
# macOS: brew install imagemagick
# Ubuntu: sudo apt-get install imagemagick

# Then generate icons from your logo
convert logo.png -resize 16x16 icon16.png
convert logo.png -resize 48x48 icon48.png
convert logo.png -resize 128x128 icon128.png
```

### Option 3: Using Photoshop/GIMP

1. Create a new canvas with the required dimensions
2. Design your icon
3. Export as PNG
4. Save with the correct filename

## Design Guidelines

- **Simple and recognizable** at small sizes
- **High contrast** for visibility
- **Professional look** matching your brand
- **Transparent background** (optional but recommended)

## Suggested Icon Ideas

Since this is a LinkedIn matching tool, consider:
- 🤝 Handshake symbol
- 👥 Network/connection icon
- 🎯 Target with checkmark
- 💼 Briefcase with connections
- ⚡ Lightning bolt (for "match")

## Temporary Placeholder

For testing, you can use simple colored squares:
- 16x16 blue square
- 48x48 blue square
- 128x128 blue square

Until you create proper icons, the extension will show Chrome's default icon.
