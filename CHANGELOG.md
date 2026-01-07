# Changelog

All notable changes to imgshift will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-01-07

### Added
- **Dual-Engine SVG Rendering Architecture**
  - Integrated `resvg-py` as primary production-grade SVG renderer (required dependency)
  - Retained pure-Python engine as fallback for edge cases
  - Added `engine` parameter to `convert()` function with three modes:
    - `auto`: Try resvg first, fallback to Python (default)
    - `resvg`: Use resvg only (production)
    - `python`: Use pure-Python engine only (experimental)
  - CLI support: `--engine` flag for explicit engine selection

- **Comprehensive Testing Suite**
  - Added `test_all_formats.py`: Tests all format combinations (SVG↔PNG↔JPG↔WEBP)
  - Added `test_real_logos.py`: Tests with 11 real-world production logos
  - HTML report generation for visual validation
  - 100% success rate on real-world logo testing
  - 82.4% success rate on comprehensive format testing

- **Engine Abstraction Layer**
  - `SvgEngine` abstract base class for consistent interface
  - `RGBAImage` container for pixel data
  - `SvgRenderError` and `SvgEngineNotAvailableError` exceptions
  - Clean separation between rendering and file I/O

### Changed
- SVG rendering now defaults to `resvg` when available, with automatic fallback
- Updated package description to emphasize SVG support
- Removed debug print statements for cleaner production output

### Fixed
- SVG rendering accuracy improved with resvg integration
- Unicode encoding issues in test scripts (Windows compatibility)
- HTML report generation with proper UTF-8 encoding

### Technical Details
- `resvg-py>=0.2.0` added as required dependency
- Engine dispatcher in `svg/render.py` with fallback logic
- Loud warnings when falling back from resvg to Python engine
- No silent failures - all degradation is logged

## [0.1.1] - 2026-01-06

### Fixed
- SVG parser improvements
- Path handling fixes

## [0.1.0] - 2026-01-06

### Added
- Initial release
- Support for PNG, JPG, WEBP, PDF, SVG formats
- Pure-Python SVG rasterizer
- CLI interface
- Image upscaling with Lanczos/bicubic/bilinear methods
