"""
PNG format handler using pypng (pure Python).
"""

from pathlib import Path
from typing import List, Tuple, Optional, BinaryIO
import png  # pypng


class PNGHandler:
    """Handler for PNG format using pypng."""
    
    @staticmethod
    def read(source: str | Path | BinaryIO) -> Tuple[List[List[Tuple[int, int, int, int]]], int, int]:
        """
        Read a PNG file.
        
        Args:
            source: File path or file-like object
            
        Returns:
            Tuple of (rows, width, height) where rows is list of RGBA tuples
        """
        if isinstance(source, (str, Path)):
            reader = png.Reader(filename=str(source))
        else:
            reader = png.Reader(file=source)
        
        # Use asRGBA8() to automatically handle all PNG types:
        # - Palette-indexed (mode P) -> converts to RGBA
        # - Greyscale -> converts to RGBA  
        # - RGB -> adds alpha channel
        # - RGBA -> passes through
        # This normalizes all input to 8-bit RGBA format
        width, height, rows_iter, metadata = reader.asRGBA8()
        
        rows = []
        for row in rows_iter:
            row_list = list(row)
            pixel_row = []
            # Now always RGBA (4 values per pixel)
            for i in range(0, len(row_list), 4):
                r = row_list[i]
                g = row_list[i + 1]
                b = row_list[i + 2]
                a = row_list[i + 3]
                pixel_row.append((r, g, b, a))
            rows.append(pixel_row)
        
        return rows, width, height
    
    @staticmethod
    def write(dest: str | Path | BinaryIO, 
              rows: List[List[Tuple[int, int, int, int]]],
              width: int = None, height: int = None,
              compression: int = 9):
        """
        Write a PNG file.
        
        Args:
            dest: File path or file-like object
            rows: List of rows, each row is a list of RGBA tuples
            width: Image width (optional, derived from rows if not provided)
            height: Image height (optional, derived from rows if not provided)
            compression: Compression level 0-9
        """
        # Derive dimensions from actual row data
        height = len(rows)
        width = len(rows[0]) if rows else 0
        
        # Convert rows to flat RGBA format
        flat_rows = []
        for row in rows:
            flat_row = []
            for r, g, b, a in row:
                flat_row.extend([r, g, b, a])
            flat_rows.append(flat_row)
        
        # Write PNG - explicitly set RGBA mode (4 channels)
        writer = png.Writer(
            width=width, 
            height=height, 
            greyscale=False,
            alpha=True, 
            bitdepth=8,
            compression=compression
        )
        
        if isinstance(dest, (str, Path)):
            with open(dest, 'wb') as f:
                writer.write(f, flat_rows)
        else:
            writer.write(dest, flat_rows)
    
    @staticmethod
    def from_pixel_buffer(buffer) -> Tuple[List[List[Tuple[int, int, int, int]]], int, int]:
        """
        Convert a PixelBuffer to PNG-compatible format.
        
        Args:
            buffer: PixelBuffer from rasterizer
            
        Returns:
            Tuple of (rows, width, height)
        """
        return buffer.get_rows(), buffer.width, buffer.height
