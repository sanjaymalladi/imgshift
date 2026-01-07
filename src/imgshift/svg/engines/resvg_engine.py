"""
Resvg-based SVG rendering engine.

This is the primary, production-grade SVG renderer.
Requires resvg-python to be installed.
"""

from pathlib import Path
from .base import SvgEngine, RGBAImage
from .exceptions import SvgRenderError, SvgEngineNotAvailableError


class ResvgEngine(SvgEngine):
    """SVG renderer using resvg library."""
    
    def __init__(self):
        """Initialize resvg engine."""
        try:
            import resvg_py
            self._resvg = resvg_py
        except ImportError:
            raise SvgEngineNotAvailableError(
                "resvg-py is not installed. "
                "Install with: pip install imgshift[svg]"
            )
    
    @property
    def name(self) -> str:
        return "resvg"
    
    def render(self, svg_source: str, width: int = None, height: int = None) -> RGBAImage:
        """
        Render SVG using resvg.
        
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
            # Load SVG data
            svg_path = Path(svg_source)
            if svg_path.exists():
                with open(svg_path, 'r', encoding='utf-8') as f:
                    svg_str = f.read()
            else:
                # Assume it's SVG string content
                svg_str = svg_source if isinstance(svg_source, str) else svg_source.decode('utf-8')
            
            # Render with resvg-py using svg_to_bytes
            # This returns PNG bytes
            png_data = self._resvg.svg_to_bytes(svg_str)
            
            # Convert PNG to RGBA
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(png_data))
            
            # Resize if requested
            if width is not None or height is not None:
                target_width = width if width is not None else int(img.width * (height / img.height))
                target_height = height if height is not None else int(img.height * (width / img.width))
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Ensure RGBA
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            return RGBAImage(
                width=img.width,
                height=img.height,
                data=img.tobytes()
            )
            
        except Exception as e:
            raise SvgRenderError(f"resvg rendering failed: {e}")
