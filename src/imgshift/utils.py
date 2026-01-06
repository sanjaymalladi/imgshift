"""
Utility functions for format detection, color parsing, and validation.
"""

from pathlib import Path
from typing import Tuple, Optional
import re


# Supported format extensions
RASTER_FORMATS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff', '.tif', '.ico'}
VECTOR_FORMATS = {'.svg'}
DOCUMENT_FORMATS = {'.pdf'}
ALL_FORMATS = RASTER_FORMATS | VECTOR_FORMATS | DOCUMENT_FORMATS


def detect_format(path: str | Path) -> str:
    """
    Detect the image format from file extension.
    
    Args:
        path: File path
        
    Returns:
        Lowercase format extension (e.g., '.png')
        
    Raises:
        ValueError: If format is not supported
    """
    ext = Path(path).suffix.lower()
    if ext not in ALL_FORMATS:
        raise ValueError(f"Unsupported format: {ext}")
    return ext


def is_raster(path: str | Path) -> bool:
    """Check if the file is a raster image format."""
    return Path(path).suffix.lower() in RASTER_FORMATS


def is_vector(path: str | Path) -> bool:
    """Check if the file is a vector format (SVG)."""
    return Path(path).suffix.lower() in VECTOR_FORMATS


def is_pdf(path: str | Path) -> bool:
    """Check if the file is a PDF."""
    return Path(path).suffix.lower() == '.pdf'


def parse_color(color: str) -> Tuple[int, int, int, int]:
    """
    Parse a color string into RGBA tuple.
    
    Supports:
        - Hex: #RGB, #RRGGBB, #RRGGBBAA
        - Named colors: red, blue, green, etc.
        - rgb(r, g, b), rgba(r, g, b, a)
        - none (transparent)
    
    Args:
        color: Color string
        
    Returns:
        Tuple of (R, G, B, A) with values 0-255
    """
    if not color or color.lower() == 'none':
        return (0, 0, 0, 0)
    
    color = color.strip().lower()
    
    # Named colors
    named_colors = {
        'black': (0, 0, 0, 255),
        'white': (255, 255, 255, 255),
        'red': (255, 0, 0, 255),
        'green': (0, 128, 0, 255),
        'blue': (0, 0, 255, 255),
        'yellow': (255, 255, 0, 255),
        'cyan': (0, 255, 255, 255),
        'magenta': (255, 0, 255, 255),
        'gray': (128, 128, 128, 255),
        'grey': (128, 128, 128, 255),
        'orange': (255, 165, 0, 255),
        'purple': (128, 0, 128, 255),
        'pink': (255, 192, 203, 255),
        'brown': (165, 42, 42, 255),
        'lime': (0, 255, 0, 255),
        'navy': (0, 0, 128, 255),
        'teal': (0, 128, 128, 255),
        'olive': (128, 128, 0, 255),
        'maroon': (128, 0, 0, 255),
        'aqua': (0, 255, 255, 255),
        'silver': (192, 192, 192, 255),
        'transparent': (0, 0, 0, 0),
    }
    
    if color in named_colors:
        return named_colors[color]
    
    # Hex colors
    if color.startswith('#'):
        hex_val = color[1:]
        if len(hex_val) == 3:
            r = int(hex_val[0] * 2, 16)
            g = int(hex_val[1] * 2, 16)
            b = int(hex_val[2] * 2, 16)
            return (r, g, b, 255)
        elif len(hex_val) == 6:
            r = int(hex_val[0:2], 16)
            g = int(hex_val[2:4], 16)
            b = int(hex_val[4:6], 16)
            return (r, g, b, 255)
        elif len(hex_val) == 8:
            r = int(hex_val[0:2], 16)
            g = int(hex_val[2:4], 16)
            b = int(hex_val[4:6], 16)
            a = int(hex_val[6:8], 16)
            return (r, g, b, a)
    
    # rgb() / rgba()
    rgb_match = re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)', color)
    if rgb_match:
        r = int(rgb_match.group(1))
        g = int(rgb_match.group(2))
        b = int(rgb_match.group(3))
        a = int(float(rgb_match.group(4) or 1) * 255)
        return (min(255, r), min(255, g), min(255, b), min(255, a))
    
    # Default to black if parsing fails
    return (0, 0, 0, 255)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + (b - a) * t
