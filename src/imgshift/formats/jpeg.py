"""
JPEG format handler using Pillow.

JPEG encoding/decoding is complex (DCT, Huffman coding), so we use Pillow
for this format only.
"""

from pathlib import Path
from typing import List, Tuple, BinaryIO
from PIL import Image as PILImage
import io


class JPEGHandler:
    """Handler for JPEG format using Pillow."""
    
    @staticmethod
    def read(source: str | Path | BinaryIO) -> Tuple[List[List[Tuple[int, int, int, int]]], int, int]:
        """
        Read a JPEG file.
        
        Args:
            source: File path or file-like object
            
        Returns:
            Tuple of (rows, width, height) where rows is list of RGBA tuples
        """
        if isinstance(source, (str, Path)):
            img = PILImage.open(source)
        else:
            img = PILImage.open(source)
        
        # Convert to RGBA
        img = img.convert('RGBA')
        width, height = img.size
        
        # Get pixel data
        pixels = list(img.getdata())
        
        rows = []
        for y in range(height):
            row = pixels[y * width:(y + 1) * width]
            rows.append(list(row))
        
        return rows, width, height
    
    @staticmethod
    def write(dest: str | Path | BinaryIO,
              rows: List[List[Tuple[int, int, int, int]]],
              width: int, height: int,
              quality: int = 85):
        """
        Write a JPEG file.
        
        Args:
            dest: File path or file-like object
            rows: List of rows, each row is a list of RGBA tuples
            width: Image width
            height: Image height
            quality: JPEG quality 1-100
        """
        # Derive dimensions from actual row data
        height = len(rows)
        width = len(rows[0]) if rows else 0
        
        # Create PIL image
        img = PILImage.new('RGB', (width, height))
        
        # Set pixels (convert RGBA to RGB)
        pixels = []
        for row in rows:
            for r, g, b, a in row:
                pixels.append((r, g, b))
        
        img.putdata(pixels)
        
        # Save
        if isinstance(dest, (str, Path)):
            img.save(dest, 'JPEG', quality=quality)
        else:
            img.save(dest, 'JPEG', quality=quality)
    
    @staticmethod
    def read_other_raster(source: str | Path) -> Tuple[List[List[Tuple[int, int, int, int]]], int, int]:
        """
        Read other raster formats (WebP, GIF, BMP, TIFF, ICO) using Pillow.
        
        Args:
            source: File path
            
        Returns:
            Tuple of (rows, width, height)
        """
        img = PILImage.open(source)
        img = img.convert('RGBA')
        width, height = img.size
        
        pixels = list(img.getdata())
        
        rows = []
        for y in range(height):
            row = pixels[y * width:(y + 1) * width]
            rows.append(list(row))
        
        return rows, width, height
    
    @staticmethod
    def write_other_raster(dest: str | Path,
                           rows: List[List[Tuple[int, int, int, int]]],
                           width: int, height: int,
                           format: str,
                           **kwargs):
        """
        Write other raster formats using Pillow.
        
        Args:
            dest: File path
            rows: List of rows, each row is a list of RGBA tuples
            width: Image width
            height: Image height
            format: Format name (WebP, GIF, BMP, TIFF, ICO)
            **kwargs: Additional format-specific options
        """
        # Derive dimensions from actual row data
        height = len(rows)
        width = len(rows[0]) if rows else 0
        
        # Create PIL image with alpha
        img = PILImage.new('RGBA', (width, height))
        
        # Set pixels
        pixels = []
        for row in rows:
            pixels.extend(row)
        
        img.putdata(pixels)
        
        # Handle format-specific requirements
        if format.upper() in ('JPEG', 'JPG', 'BMP'):
            # These don't support alpha
            img = img.convert('RGB')
        
        # Save with appropriate options
        save_kwargs = {}
        
        if format.upper() == 'WEBP':
            save_kwargs['quality'] = kwargs.get('quality', 85)
        elif format.upper() == 'GIF':
            # GIF requires palette mode
            img = img.convert('P', palette=PILImage.ADAPTIVE, colors=256)
        elif format.upper() in ('TIFF', 'TIF'):
            save_kwargs['compression'] = kwargs.get('compression', 'tiff_deflate')
        elif format.upper() == 'ICO':
            # ICO may need size adjustment
            pass
        
        img.save(dest, format=format.upper(), **save_kwargs)
