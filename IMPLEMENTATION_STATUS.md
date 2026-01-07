# imgshift: Implementation Status & Architecture

This document provides a comprehensive overview of the current implementation of `imgshift`, a pure-Python high-performance image converter.

## 1. Core Architecture

The `imgshift` library follows a modular architecture designed for extensibility and ease of use. The core philosophy is to provide a unified `convert()` API that delegates to specialized handlers based on source and target formats.

### Main Components
- **`core.py`**: The central entry point.
    - `convert()`: High-level function handling format detection, loading, resizing, and saving.
    - `Image` class: A fluent API wrapper around `convert()` (e.g., `Image("src.svg").resize(500).save("out.png")`).
    - `upscale()`: Function dedicated to high-quality image upscaling using Lanczos/Bicubic resampling.
- **`cli.py`**: Command-line interface integration.
- **`/formats`**: Modules handling specific file formats (PDF, PNG, JPEG).
- **`/svg`**: A largely custom-built SVG rendering engine.

## 2. The Custom SVG Engine (`/src/imgshift/svg`)

One of the most significant components of `imgshift` is its zero-dependency (native Python) SVG rendering engine. Instead of relying on heavy C libraries like `librsvg` or `Cairo`, `imgshift` implements its own parsing and rasterization pipeline.

### 2.1 Parsing Pipeline (`parser.py`, `elements.py`, `path_parser.py`)
- **XML Parsing**: Uses `xml.etree.ElementTree` to traverse the SVG DOM.
- **Element Model**: Maps SVG tags to Python dataclasses (`Rect`, `Circle`, `Path`, `Group`, etc.) defined in `elements.py`.
- **Attribute Parsing**:
    - **Transforms**: Parses standard SVG transform strings (translate, scale, rotate, matrix) into 3x3 affine transformation matrices (`Matrix` class).
    - **Units**: Handles `px`, `pt`, `mm`, `cm`, `in`, `%`, and unitless numbers.
    - **Path Data (`d`)**: A dedicated recursive descent parser in `path_parser.py` handles all SVG path commands (M, L, H, V, C, S, Q, T, A, Z), converting them into standard geometrical instruction sets.

### 2.2 Rendering Pipeline (`rasterizer.py`)
The rendering engine uses a **Scanline Rendering Algorithm**:
1.  **Tessellation**: All shapes (including circles, ellipses, and Beziers) are broken down into polygons (lists of `(x,y)` points).
    - **Adaptive Subdivision**: Cubic and Quadratic Bezier curves are recursively subdivided until flat ensuring high precision without wasted processing on straight segments.
2.  **Transformations**:
    - **Coordinate Systems**: Handles ViewBox mapping to Output Pixel Space.
    - **Hierarchy**: Nested Group (`<g>`) transforms are compounded using matrix multiplication.
3.  **Rasterization**:
    - **Edge Table**: Builds a table of edges from the generated polygons.
    - **Active Edge List (AEL)**: Iterates scanline by scanline (Y-axis), maintaining active intersecting edges.
    - **Winding Rules**: Supports both `nonzero` and `evenodd` fill rules to determine which pixels are "inside" the shape.
    - **Anti-aliasing**: Performs alpha blending for smooth edges.
4.  **Paint & Styles**:
    - **Solid Colors**: RGBA support via `SolidColor`.
    - **Gradients**: Fully implemented `LinearGradient` and `RadialGradient` with support for `gradientTransform` and `gradientUnits="objectBoundingBox"`.
    - **Layer Blending**: Handles Group opacity by rendering the group to a temporary isolated buffer and treating it as a layer.

### 2.3 Text Rendering
Text support (`<text>`) is currently implemented by delegating to **Pillow (PIL)**.
- It calculates the precise screen position using the current transformation matrix.
- Renders the text onto a temporary PIL image and composites it onto the main buffer.

## 3. Format Handlers (`/src/imgshift/formats`)

### PDF (`pdf.py`)
- **Engine**: Wraps `PyMuPDF` (fitz).
- **Capabilities**:
    - Reading specific pages.
    - Setting DPI for rasterization.
    - Writing multi-page PDFs from a list of images.

### PNG (`png.py`)
- **Engine**: Uses `pypng` for writing.
- **Capabilities**:
    - Efficient row-based writing.
    - Full Alpha channel (RGBA) support.

### JPEG / WebP / Others
- **Engine**: Delegates entire IO to `Pillow`.
- **Capabilities**:
    - Quality control (1-100).
    - Format conversion/optimization.

## 4. Upscaling Algorithm
The `upscale()` function in `core.py` is distinct from standard resizing.
- **Algorithms**: Exposes `LANCZOS` (default, best for distinct graphics) and `BICUBIC` (smooth).
- **Logic**: Calculates target dimensions preserving aspect ratio and handles transparency compositing for formats like JPEG (composites onto white background).

## 5. Current Capabilities & Limitations

### Supported SVG Features
- [x] Basic Shapes (Rect, Circle, Ellipse, Line, Polyline, Polygon)
- [x] Paths (All standard commands, absolute & relative)
- [x] Transforms (Matrix, Translate, Scale, Rotate)
- [x] Grouping `<g>` with Opacity
- [x] Gradients (Linear, Radial)
- [x] Stroke & Fill
- [x] ViewBox & Percent-based sizing

### Known Limitations (Not Supported)
- [ ] `<image>` tag (embedding raster images inside SVG).
- [ ] `<clipPath>` and `<mask>` (complex masking).
- [ ] `<filter>` (SVG filters like blur, drop-shadow).
- [ ] Complex Text Layout (text-anchor other than start involves approximation, tspan support is minimal).
- [ ] CSS Style Sheets (only `style` attribute and presentation attributes are supported).
