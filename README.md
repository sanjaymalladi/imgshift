# imgshift

**Shift between any image format effortlessly.**

A Python library for universal image format conversion with a focus on SVG support. Built with minimal dependencies and featuring both a simple function API and a fluent class API.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## Features

- 🎨 **Universal Format Support**: Convert between PNG, JPEG, WebP, GIF, BMP, TIFF, ICO, SVG, and PDF
- 🖼️ **Custom SVG Renderer**: Built-in SVG parser and rasterizer - no Cairo or external dependencies needed
- 📐 **Smart Resizing**: Bilinear interpolation for high-quality image scaling
- 📄 **PDF Support**: Convert images to/from PDF, combine multiple images into multi-page PDFs
- 🔧 **Flexible API**: Simple one-liner functions or fluent method chaining
- 💻 **CLI Tool**: Command-line interface for batch conversions

## Installation

```bash
pip install imgshift
```

## Quick Start

### Simple Conversion

```python
from imgshift import convert

# SVG to PNG
convert("icon.svg", "icon.png")

# With specific size
convert("icon.svg", "icon.png", width=512)

# PNG to JPEG with quality
convert("photo.png", "photo.jpg", quality=90)

# PDF page to PNG
convert("document.pdf", "page.png", page=0, dpi=300)
```

### Fluent API

```python
from imgshift import Image

# Chain operations
Image("icon.svg").resize(512, 512).save("icon.png")

# With quality and DPI settings
Image("photo.png").set_quality(95).set_dpi(150).save("photo.jpg")

# PDF with specific page
Image("document.pdf").page(0).set_dpi(300).save("page.png")
```

### Multiple Images to PDF

```python
from imgshift import convert

# Combine multiple images into a PDF
convert(["page1.png", "page2.png", "page3.png"], "document.pdf")
```

## CLI Usage

```bash
# Single file conversion
imgshift input.svg output.png

# With options
imgshift input.svg output.png --width 512 --height 512

# Batch conversion
imgshift batch "*.svg" --format png --output-dir ./converted

# Multiple files to PDF
imgshift combine img1.png img2.png img3.png -o output.pdf
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--width`, `-w` | Output width in pixels |
| `--height`, `-h` | Output height in pixels |
| `--quality`, `-q` | JPEG/WebP quality (1-100, default: 85) |
| `--dpi`, `-d` | DPI for PDF/SVG rendering (default: 150) |
| `--page`, `-p` | PDF page number (0-indexed) |
| `--format`, `-f` | Output format for batch conversion |
| `--output-dir`, `-o` | Output directory for batch conversion |

## Supported Formats

| Format | Read | Write | Notes |
|--------|:----:|:-----:|-------|
| PNG | ✅ | ✅ | Lossless with alpha channel |
| JPEG | ✅ | ✅ | Lossy compression, quality 1-100 |
| WebP | ✅ | ✅ | Modern format, lossy/lossless |
| GIF | ✅ | ✅ | Palette-based, 256 colors |
| BMP | ✅ | ✅ | Uncompressed bitmap |
| TIFF | ✅ | ✅ | High-quality, supports compression |
| ICO | ✅ | ✅ | Windows icon format |
| SVG | ✅ | ❌ | Vector graphics (custom renderer) |
| PDF | ✅ | ✅ | Single or multi-page documents |

## SVG Support

imgshift includes a custom-built SVG renderer that doesn't require Cairo or other external C libraries. Supported SVG features:

### Shapes
- `<rect>` - Rectangles (including rounded corners)
- `<circle>` - Circles
- `<ellipse>` - Ellipses  
- `<line>` - Lines
- `<polyline>` - Connected line segments
- `<polygon>` - Closed polygons
- `<path>` - Full path syntax including curves

### Path Commands
- Move: `M`, `m`
- Line: `L`, `l`, `H`, `h`, `V`, `v`
- Cubic Bezier: `C`, `c`, `S`, `s`
- Quadratic Bezier: `Q`, `q`, `T`, `t`
- Arc: `A`, `a`
- Close: `Z`, `z`

### Styling
- `fill` - Fill color (hex, named colors, rgb/rgba)
- `stroke` - Stroke color
- `stroke-width` - Stroke width
- `opacity` - Element opacity
- `fill-opacity` - Fill opacity
- `stroke-opacity` - Stroke opacity

### Transforms
- `translate(x, y)`
- `rotate(angle)` or `rotate(angle, cx, cy)`
- `scale(x)` or `scale(x, y)`
- `skewX(angle)` / `skewY(angle)`
- `matrix(a, b, c, d, e, f)`

## API Reference

### `convert(source, target, **options)`

Convert an image from one format to another.

**Parameters:**
- `source`: Source file path (str or Path), or list of paths for multi-image PDF
- `target`: Target file path
- `width`: Target width (optional)
- `height`: Target height (optional)
- `quality`: JPEG/WebP quality 1-100 (default: 85)
- `dpi`: DPI for PDF/SVG rendering (default: 150)
- `page`: PDF page number, 0-indexed (optional)
- `background`: Background color tuple (R, G, B, A) for SVG (default: white)

### `Image(source)`

Fluent API for image manipulation.

**Methods:**
- `.resize(width, height)` - Set target dimensions
- `.set_quality(quality)` - Set JPEG/WebP quality
- `.set_dpi(dpi)` - Set DPI for PDF/SVG
- `.page(page_num)` - Select PDF page
- `.set_background(r, g, b, a)` - Set SVG background color
- `.save(dest)` - Save to file

## Dependencies

- **pypng** - Pure Python PNG handling
- **Pillow** - JPEG and other raster formats
- **PyMuPDF** - PDF reading and writing

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

Built with ❤️ for the Python community.
