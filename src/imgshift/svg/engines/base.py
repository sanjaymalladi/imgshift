"""
SVG rendering engine base interface.

All SVG engines must implement this contract.
"""

from abc import ABC, abstractmethod
from typing import Tuple


class RGBAImage:
    """Simple container for RGBA pixel data."""
    
    def __init__(self, width: int, height: int, data: bytes):
        """
        Initialize RGBA image.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            data: Raw RGBA bytes (width * height * 4 bytes)
        """
        self.width = width
        self.height = height
        self.data = data
        
        if len(data) != width * height * 4:
            raise ValueError(f"Data length {len(data)} doesn't match {width}x{height}x4")


class SvgEngine(ABC):
    """Abstract base class for SVG rendering engines."""
    
    @abstractmethod
    def render(self, svg_source: str, width: int = None, height: int = None) -> RGBAImage:
        """
        Render SVG to RGBA pixel data.
        
        Args:
            svg_source: Path to SVG file or SVG string content
            width: Target width in pixels (None = use SVG dimensions)
            height: Target height in pixels (None = use SVG dimensions)
            
        Returns:
            RGBAImage with rendered pixels
            
        Raises:
            SvgRenderError: If rendering fails
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Engine name for logging/debugging."""
        pass
