"""
Pure-Python SVG rendering engine.

This is a fallback/experimental renderer with limitations.
Does not require external dependencies.

Limitations:
- Complex fill rules may have scanline artifacts
- Limited text shaping support  
- No filters, clipping paths, or advanced features
- Best-effort rendering for simple SVGs
"""

from pathlib import Path
from .base import SvgEngine, RGBAImage
from .exceptions import SvgRenderError


class PythonSvgEngine(SvgEngine):
    """Pure-Python SVG renderer (limited, zero-dependency)."""
    
    @property
    def name(self) -> str:
        return "python"
    
    def render(self, svg_source: str, width: int = None, height: int = None) -> RGBAImage:
        """
        Render SVG using pure-Python implementation.
        
        Args:
            svg_source: Path to SVG file or SVG string content
            width: Target width in pixels
            height: Target height in pixels
            
        Returns:
            RGBAImage with rendered pixels
            
        Raises:
            SvgRenderError: If rendering fails
        """
        try:
            from imgshift.svg.parser import SVGParser
            from imgshift.svg.rasterizer import Rasterizer
            
            # Determine if source is file path or SVG content
            svg_path = Path(svg_source)
            if svg_path.exists() and svg_path.is_file():
                # It's a file path
                source_to_parse = svg_path
            else:
                # It's SVG string content
                source_to_parse = svg_source
            
            # Parse SVG
            parser = SVGParser()
            doc = parser.parse(source_to_parse)
            
            # Render to pixel buffer
            rasterizer = Rasterizer(antialias=True)
            buffer = rasterizer.render(doc, width=width, height=height)
            
            # Convert to RGBA bytes
            rgba_data = buffer.get_flat_rgba()
            
            return RGBAImage(
                width=buffer.width,
                height=buffer.height,
                data=rgba_data
            )
            
        except Exception as e:
            raise SvgRenderError(f"Python engine rendering failed: {e}")
