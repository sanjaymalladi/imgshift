"""
Central SVG rendering dispatcher.

Manages engine selection and fallback logic.
"""

import warnings
from typing import Optional, Literal
from .engines.base import RGBAImage
from .engines.exceptions import SvgRenderError, SvgEngineNotAvailableError

EngineType = Literal["auto", "resvg", "python"]


def render_svg(
    svg_source: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    engine: EngineType = "auto"
) -> RGBAImage:
    """
    Render SVG to RGBA pixel data.
    
    Args:
        svg_source: Path to SVG file or SVG string content
        width: Target width in pixels (None = use SVG dimensions)
        height: Target height in pixels (None = use SVG dimensions)
        engine: Rendering engine to use:
            - "auto": Try resvg, fallback to Python (default)
            - "resvg": Use resvg only (raise on failure)
            - "python": Use pure-Python engine only
            
    Returns:
        RGBAImage with rendered pixels
        
    Raises:
        SvgRenderError: If rendering fails
        SvgEngineNotAvailableError: If requested engine is not available
    """
    
    if engine == "resvg":
        # Explicit resvg request - no fallback
        from .engines.resvg_engine import ResvgEngine
        renderer = ResvgEngine()
        return renderer.render(svg_source, width, height)
    
    elif engine == "python":
        # Explicit Python engine request
        from .engines.python_engine import PythonSvgEngine
        renderer = PythonSvgEngine()
        return renderer.render(svg_source, width, height)
    
    elif engine == "auto":
        # Auto mode: try resvg first, fallback to Python
        try:
            from .engines.resvg_engine import ResvgEngine
            renderer = ResvgEngine()
            return renderer.render(svg_source, width, height)
            
        except SvgEngineNotAvailableError:
            # resvg not installed, use Python engine
            warnings.warn(
                "resvg-py not available, using pure-Python engine. "
                "Install resvg for production use: pip install imgshift[svg]",
                UserWarning
            )
            from .engines.python_engine import PythonSvgEngine
            renderer = PythonSvgEngine()
            return renderer.render(svg_source, width, height)
            
        except SvgRenderError as e:
            # resvg failed, try Python engine as fallback
            warnings.warn(
                f"resvg rendering failed ({e}), falling back to pure-Python engine. "
                "Output may have limitations.",
                UserWarning
            )
            from .engines.python_engine import PythonSvgEngine
            renderer = PythonSvgEngine()
            return renderer.render(svg_source, width, height)
    
    else:
        raise ValueError(f"Invalid engine '{engine}'. Must be 'auto', 'resvg', or 'python'")
