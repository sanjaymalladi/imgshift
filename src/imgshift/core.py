"""
Core module - Main API for image conversion.

Provides the convert() function and Image class for the fluent API.
"""

from pathlib import Path
from typing import List, Tuple, Optional, Union
from imgshift.utils import detect_format, is_raster, is_vector, is_pdf, RASTER_FORMATS
from imgshift.svg.parser import SVGParser
from imgshift.svg.rasterizer import Rasterizer, PixelBuffer
from imgshift.formats.png import PNGHandler
from imgshift.formats.jpeg import JPEGHandler
from imgshift.formats.pdf import PDFHandler


def convert(source: Union[str, Path, List[str], List[Path]], 
            target: Union[str, Path],
            width: Optional[int] = None,
            height: Optional[int] = None,
            quality: int = 85,
            dpi: int = 150,
            page: Optional[int] = None,
            background: Tuple[int, int, int, int] = (255, 255, 255, 255),
            engine: str = "auto",
            **kwargs) -> None:
    """
    Convert image(s) from one format to another.
    
    Args:
        source: Source file path, or list of paths for multi-image PDF
        target: Target file path
        width: Target width (optional)
        height: Target height (optional)
        quality: JPEG quality 1-100 (default 85)
        dpi: DPI for PDF/SVG rendering (default 150)
        page: Specific PDF page to convert (0-indexed, None for all)
        background: Background color for SVG rendering (R, G, B, A)
        engine: SVG rendering engine - 'auto' (try resvg, fallback to python), 
                'resvg' (production), or 'python' (experimental fallback)
        **kwargs: Additional format-specific options
        
    Examples:
        # Simple conversion
        convert("icon.svg", "icon.png")
        
        # SVG to PNG with size
        convert("icon.svg", "icon.png", width=512)
        
        # Use specific engine
        convert("logo.svg", "logo.png", engine="resvg")
        
        # PNG to JPEG with quality
        convert("photo.png", "photo.jpg", quality=90)
        
        # PDF page to PNG
        convert("doc.pdf", "page.png", page=0, dpi=300)
        
        # Multiple images to PDF
        convert(["img1.png", "img2.png"], "output.pdf")
    """
    target_path = Path(target)
    target_format = detect_format(target_path)
    
    # Handle multiple source files (for creating PDF)
    if isinstance(source, list):
        _convert_multiple_to_pdf(source, target_path, dpi, engine)
        return
    
    source_path = Path(source)
    source_format = detect_format(source_path)
    
    # Load source image
    rows, src_width, src_height = _load_image(
        source_path, source_format, width, height, dpi, page, background, engine
    )
    
    # Apply resize if needed
    if width or height:
        rows, src_width, src_height = _resize(rows, src_width, src_height, width, height)
    
    # Save to target format
    _save_image(target_path, target_format, rows, src_width, src_height, quality, dpi, **kwargs)


def upscale(source: Union[str, Path],
            target: Union[str, Path],
            scale: Optional[float] = None,
            width: Optional[int] = None,
            height: Optional[int] = None,
            method: str = 'lanczos',
            quality: int = 95,
            **kwargs) -> None:
    """
    Upscale an image to higher resolution using high-quality interpolation.
    
    This uses traditional resampling algorithms (no AI) for clean, sharp upscaling.
    Best for logos, icons, and graphics where you want to preserve exact appearance.
    
    Args:
        source: Source image path (PNG, WEBP, JPEG, etc.)
        target: Target image path
        scale: Scale factor (e.g., 2.0 for 2x, 4.0 for 4x). Either scale or width/height required.
        width: Target width in pixels (optional, maintains aspect ratio if height not specified)
        height: Target height in pixels (optional, maintains aspect ratio if width not specified)
        method: Resampling method - 'lanczos' (sharpest), 'bicubic', 'bilinear', 'nearest'
        quality: Output quality 1-100 for lossy formats (default 95)
        **kwargs: Additional format-specific options
        
    Examples:
        # Upscale 2x with Lanczos (best for logos)
        upscale("logo_small.png", "logo_large.png", scale=2)
        
        # Upscale to specific dimensions
        upscale("icon.webp", "icon_hd.png", width=1024, height=1024)
        
        # Upscale 4x with bicubic
        upscale("photo.jpg", "photo_4x.jpg", scale=4, method='bicubic')
        
    Raises:
        ValueError: If neither scale nor width/height is specified
        ValueError: If source format is not supported
    """
    from PIL import Image as PILImage
    
    # Validate inputs
    if scale is None and width is None and height is None:
        raise ValueError("Must specify either 'scale' or 'width'/'height'")
    
    # Resampling method mapping
    resampling_methods = {
        'lanczos': PILImage.Resampling.LANCZOS,
        'bicubic': PILImage.Resampling.BICUBIC,
        'bilinear': PILImage.Resampling.BILINEAR,
        'nearest': PILImage.Resampling.NEAREST,
    }
    
    if method.lower() not in resampling_methods:
        raise ValueError(f"Unknown method '{method}'. Use: lanczos, bicubic, bilinear, nearest")
    
    resample = resampling_methods[method.lower()]
    
    # Load source image with Pillow
    source_path = Path(source)
    target_path = Path(target)
    
    img = PILImage.open(source_path)
    
    # Preserve transparency if present
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        img = img.convert('RGBA')
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    orig_width, orig_height = img.size
    
    # Calculate target dimensions
    if scale is not None:
        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)
    elif width is not None and height is not None:
        new_width = width
        new_height = height
    elif width is not None:
        new_width = width
        new_height = int(orig_height * (width / orig_width))
    else:  # height is not None
        new_height = height
        new_width = int(orig_width * (height / orig_height))
    
    # Ensure minimum size
    new_width = max(1, new_width)
    new_height = max(1, new_height)
    
    # Perform upscale
    upscaled = img.resize((new_width, new_height), resample=resample)
    
    # Determine output format
    target_ext = target_path.suffix.lower()
    
    # Save with appropriate settings
    save_kwargs = {}
    
    if target_ext in ('.jpg', '.jpeg'):
        if upscaled.mode == 'RGBA':
            # JPEG doesn't support transparency - composite onto white
            background = PILImage.new('RGB', upscaled.size, (255, 255, 255))
            background.paste(upscaled, mask=upscaled.split()[3])
            upscaled = background
        save_kwargs['quality'] = quality
        save_kwargs['optimize'] = True
    elif target_ext == '.png':
        save_kwargs['optimize'] = True
    elif target_ext == '.webp':
        save_kwargs['quality'] = quality
        save_kwargs['lossless'] = quality >= 100
    
    # Merge any additional kwargs
    save_kwargs.update(kwargs)
    
    upscaled.save(target_path, **save_kwargs)


def _load_image(source: Path, format: str, 
                width: Optional[int], height: Optional[int],
                dpi: int, page: Optional[int],
                background: Tuple[int, int, int, int],
                engine: str = "auto") -> Tuple[List[List[Tuple[int, int, int, int]]], int, int]:
    """Load an image from a file."""
    
    if format == '.svg':
        # Use new dual-engine dispatcher
        from imgshift.svg.render import render_svg
        
        rgba_image = render_svg(str(source), width=width, height=height, engine=engine)
        
        # Convert RGBAImage to rows format
        rows = []
        for y in range(rgba_image.height):
            row = []
            for x in range(rgba_image.width):
                idx = (y * rgba_image.width + x) * 4
                r, g, b, a = rgba_image.data[idx:idx+4]
                row.append((r, g, b, a))
            rows.append(row)
        
        return rows, rgba_image.width, rgba_image.height
    
    elif format == '.pdf':
        # Use PDF handler
        if page is not None:
            return PDFHandler.read_page(source, page, dpi)
        else:
            # Return first page by default
            return PDFHandler.read_page(source, 0, dpi)
    
    elif format == '.png':
        return PNGHandler.read(source)
    
    elif format in ('.jpg', '.jpeg'):
        return JPEGHandler.read(source)
    
    else:
        # Use Pillow for other raster formats
        return JPEGHandler.read_other_raster(source)


def _save_image(dest: Path, format: str,
                rows: List[List[Tuple[int, int, int, int]]],
                width: int, height: int,
                quality: int, dpi: int, **kwargs):
    """Save an image to a file."""
    
    if format == '.png':
        PNGHandler.write(dest, rows, width, height)
    
    elif format in ('.jpg', '.jpeg'):
        JPEGHandler.write(dest, rows, width, height, quality)
    
    elif format == '.pdf':
        PDFHandler.write_single(dest, rows, width, height, dpi)
    
    else:
        # Use Pillow for other raster formats
        fmt_map = {
            '.webp': 'WEBP',
            '.gif': 'GIF',
            '.bmp': 'BMP',
            '.tiff': 'TIFF',
            '.tif': 'TIFF',
            '.ico': 'ICO',
        }
        pil_format = fmt_map.get(format, format.upper().lstrip('.'))
        JPEGHandler.write_other_raster(dest, rows, width, height, pil_format, quality=quality, **kwargs)


def _convert_multiple_to_pdf(sources: List[Union[str, Path]], 
                             dest: Path, dpi: int, engine: str = "auto"):
    """Convert multiple images to a multi-page PDF."""
    images = []
    
    for source in sources:
        source_path = Path(source)
        source_format = detect_format(source_path)
        rows, width, height = _load_image(
            source_path, source_format, None, None, dpi, None, (255, 255, 255, 255), engine
        )
        images.append((rows, width, height))
    
    PDFHandler.write(dest, images, dpi)


def _resize(rows: List[List[Tuple[int, int, int, int]]], 
            src_width: int, src_height: int,
            target_width: Optional[int], 
            target_height: Optional[int]) -> Tuple[List[List[Tuple[int, int, int, int]]], int, int]:
    """Resize image using bilinear interpolation."""
    # Calculate target dimensions
    if target_width and target_height:
        new_width, new_height = target_width, target_height
    elif target_width:
        aspect = src_height / src_width
        new_width = target_width
        new_height = int(target_width * aspect)
    elif target_height:
        aspect = src_width / src_height
        new_height = target_height
        new_width = int(target_height * aspect)
    else:
        return rows, src_width, src_height
    
    # Bilinear interpolation
    new_rows = []
    
    for y in range(new_height):
        row = []
        src_y = y * (src_height - 1) / max(1, new_height - 1)
        y0 = int(src_y)
        y1 = min(y0 + 1, src_height - 1)
        y_frac = src_y - y0
        
        for x in range(new_width):
            src_x = x * (src_width - 1) / max(1, new_width - 1)
            x0 = int(src_x)
            x1 = min(x0 + 1, src_width - 1)
            x_frac = src_x - x0
            
            # Get four neighboring pixels
            p00 = rows[y0][x0]
            p01 = rows[y0][x1]
            p10 = rows[y1][x0]
            p11 = rows[y1][x1]
            
            # Interpolate
            r = int((1-y_frac) * ((1-x_frac) * p00[0] + x_frac * p01[0]) + 
                    y_frac * ((1-x_frac) * p10[0] + x_frac * p11[0]))
            g = int((1-y_frac) * ((1-x_frac) * p00[1] + x_frac * p01[1]) + 
                    y_frac * ((1-x_frac) * p10[1] + x_frac * p11[1]))
            b = int((1-y_frac) * ((1-x_frac) * p00[2] + x_frac * p01[2]) + 
                    y_frac * ((1-x_frac) * p10[2] + x_frac * p11[2]))
            a = int((1-y_frac) * ((1-x_frac) * p00[3] + x_frac * p01[3]) + 
                    y_frac * ((1-x_frac) * p10[3] + x_frac * p11[3]))
            
            row.append((r, g, b, a))
        
        new_rows.append(row)
    
    return new_rows, new_width, new_height


class Image:
    """
    Fluent API for image manipulation.
    
    Example:
        Image("icon.svg").resize(512, 512).save("icon.png")
    """
    
    def __init__(self, source: Union[str, Path]):
        """
        Load an image.
        
        Args:
            source: Path to image file
        """
        self.source_path = Path(source)
        self.source_format = detect_format(self.source_path)
        
        # Default options
        self._width: Optional[int] = None
        self._height: Optional[int] = None
        self._quality: int = 85
        self._dpi: int = 150
        self._page: Optional[int] = None
        self._background: Tuple[int, int, int, int] = (255, 255, 255, 255)
        
        # Lazy-loaded image data
        self._rows: Optional[List[List[Tuple[int, int, int, int]]]] = None
        self._loaded_width: Optional[int] = None
        self._loaded_height: Optional[int] = None
    
    def resize(self, width: Optional[int] = None, 
               height: Optional[int] = None) -> 'Image':
        """
        Set target dimensions.
        
        Args:
            width: Target width
            height: Target height
            
        Returns:
            Self for chaining
        """
        self._width = width
        self._height = height
        return self
    
    def set_quality(self, quality: int) -> 'Image':
        """
        Set JPEG quality.
        
        Args:
            quality: Quality 1-100
            
        Returns:
            Self for chaining
        """
        self._quality = quality
        return self
    
    def set_dpi(self, dpi: int) -> 'Image':
        """
        Set DPI for PDF/SVG rendering.
        
        Args:
            dpi: DPI value
            
        Returns:
            Self for chaining
        """
        self._dpi = dpi
        return self
    
    def page(self, page_num: int) -> 'Image':
        """
        Select a specific PDF page.
        
        Args:
            page_num: Page number (0-indexed)
            
        Returns:
            Self for chaining
        """
        self._page = page_num
        return self
    
    def set_background(self, r: int, g: int, b: int, a: int = 255) -> 'Image':
        """
        Set background color for SVG rendering.
        
        Args:
            r, g, b, a: RGBA values 0-255
            
        Returns:
            Self for chaining
        """
        self._background = (r, g, b, a)
        return self
    
    def compress(self, quality: int) -> 'Image':
        """Alias for set_quality()."""
        return self.set_quality(quality)
    
    def save(self, dest: Union[str, Path], **kwargs) -> None:
        """
        Save the image to a file.
        
        Args:
            dest: Destination file path
            **kwargs: Additional format-specific options
        """
        convert(
            self.source_path, 
            dest,
            width=self._width,
            height=self._height,
            quality=self._quality,
            dpi=self._dpi,
            page=self._page,
            background=self._background,
            **kwargs
        )
