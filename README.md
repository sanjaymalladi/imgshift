# imgshift

**Shift between any image format effortlessly.**

A high-performance Python library for universal image format conversion with **exceptional SVG support**. Features dual-engine SVG rendering (production-grade resvg + pure-Python fallback) and supports all major image formats.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## Features

- 🎨 **Universal Format Support**: Convert between PNG, JPEG, WebP, GIF, BMP, TIFF, ICO, SVG, and PDF
- � **Dual-Engine SVG Rendering**: Production-grade `resvg` engine with pure-Python fallback
- 🔧 **Flexible Engine Selection**: Choose between `auto` (smart fallback), `resvg` (production), or `python` (experimental)
- 📐 **Smart Upscaling**: Lanczos/bicubic/bilinear interpolation for high-quality image scaling  
- 📄 **PDF Support**: Convert images to/from PDF, combine multiple images into multi-page PDFs
- 🔧 **Flexible API**: Simple one-liner functions or fluent method chaining
- 💻 **CLI Tool**: Command-line interface with engine selection support

## Installation

```bash
pip install imgshift
```

This installs all dependencies including `resvg-py` for production-grade SVG rendering.

## Quick Start

### Simple Conversion

```python
from imgshift import convert

# SVG to PNG (uses best available engine)
convert("icon.svg", "icon.png")

# With specific size
convert("icon.svg", "icon.png", width=512)

# Use specific SVG engine
convert("logo.svg", "logo.png", engine="resvg")  # Production quality
convert("simple.svg", "simple.png", engine="python")  # Zero dependencies

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

# Choose SVG engine
imgshift logo.svg logo.png --engine resvg  # Production quality
imgshift icon.svg icon.png --engine python  # Pure Python

# Batch conversion
imgshift *.svg --to png --output-dir ./converted

# Multiple files to PDF
imgshift img1.png img2.png img3.png -o output.pdf
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--width`, `-w` | Output width in pixels |
| `--height`, `-H` | Output height in pixels |
| `--quality`, `-q` | JPEG/WebP quality (1-100, default: 85) |
| `--dpi`, `-d` | DPI for PDF/SVG rendering (default: 150) |
| `--page`, `-p` | PDF page number (0-indexed) |
| `--engine` | SVG engine: `auto`, `resvg`, or `python` |
| `--to`, `-t` | Target format for batch conversion |
| `--output-dir`, `-o` | Output directory |

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

## SVG Rendering

imgshift uses a **dual-engine architecture** for SVG rendering:

### Primary Engine: `resvg` (Production)

The `resvg` engine (installed by default) provides:
- ✅ Full SVG 1.1 specification compliance
- ✅ Complex gradients, patterns, and filters
- ✅ Advanced path operations and clipping
- ✅ Production-grade accuracy (used by major tools)
- ✅ Rust-powered performance

**Default**: Used automatically for best quality.

### Fallback Engine: `python` (Experimental)

The pure-Python engine provides:
- ✅ Zero external dependencies (if you uninstall resvg-py)
- ✅ Basic SVG shapes and paths
- ✅ Transforms and styling
- ⚠️ Limited support for advanced features
- ⚠️ May have rendering artifacts on complex SVGs

**Use when**: You need to avoid compiled dependencies or rendering very simple SVGs.

### Engine Selection

```python
# Auto mode (default): tries resvg, falls back to python
convert("logo.svg", "logo.png", engine="auto")

# Explicit resvg (production)
convert("complex.svg", "complex.png", engine="resvg")

# Explicit python (zero dependencies)
convert("simple.svg", "simple.png", engine="python")
```

**Default behavior**: `resvg` is used automatically. You can explicitly choose the pure-Python engine if needed.

## Supported SVG Features

### Python Engine Support

#### Shapes
- `<rect>` - Rectangles (including rounded corners)
- `<circle>` - Circles
- `<ellipse>` - Ellipses  
- `<line>` - Lines
- `<polyline>` - Connected line segments
- `<polygon>` - Closed polygons
- `<path>` - Full path syntax including curves
- `<text>` - Basic text rendering

#### Path Commands
- Move: `M`, `m`
- Line: `L`, `l`, `H`, `h`, `V`, `v`
- Cubic Bezier: `C`, `c`, `S`, `s`
- Quadratic Bezier: `Q`, `q`, `T`, `t`
- Arc: `A`, `a`
- Close: `Z`, `z`

#### Styling
- `fill` - Fill color (hex, named colors, rgb/rgba)
- `stroke` - Stroke color
- `stroke-width` - Stroke width
- `opacity` - Element opacity
- `fill-opacity` - Fill opacity
- `stroke-opacity` - Stroke opacity

#### Transforms
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
- `engine`: SVG rendering engine: `"auto"`, `"resvg"`, or `"python"` (default: `"auto"`)

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
- **resvg-py** - Production-grade SVG rendering

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

Built with ❤️ for the Python community.
