"""
PDF format handler using PyMuPDF.
"""

from pathlib import Path
from typing import List, Tuple, Optional, Union
import fitz  # PyMuPDF


class PDFHandler:
    """Handler for PDF format using PyMuPDF."""
    
    @staticmethod
    def read_page(source: str | Path, page_num: int = 0, 
                  dpi: int = 150) -> Tuple[List[List[Tuple[int, int, int, int]]], int, int]:
        """
        Read a single page from a PDF file.
        
        Args:
            source: PDF file path
            page_num: Page number (0-indexed)
            dpi: Resolution in DPI
            
        Returns:
            Tuple of (rows, width, height) where rows is list of RGBA tuples
        """
        doc = fitz.open(source)
        
        if page_num >= len(doc):
            raise ValueError(f"Page {page_num} does not exist. PDF has {len(doc)} pages.")
        
        page = doc[page_num]
        
        # Calculate matrix for desired DPI
        zoom = dpi / 72  # PDF default is 72 DPI
        matrix = fitz.Matrix(zoom, zoom)
        
        # Render page to pixmap
        pixmap = page.get_pixmap(matrix=matrix, alpha=True)
        
        width = pixmap.width
        height = pixmap.height
        
        # Get pixel data
        samples = pixmap.samples
        
        rows = []
        stride = pixmap.stride
        n = pixmap.n  # Number of components per pixel
        
        for y in range(height):
            row = []
            for x in range(width):
                idx = y * stride + x * n
                if n == 4:  # RGBA
                    r, g, b, a = samples[idx:idx + 4]
                elif n == 3:  # RGB
                    r, g, b = samples[idx:idx + 3]
                    a = 255
                elif n == 1:  # Greyscale
                    g = samples[idx]
                    r, g, b, a = g, g, g, 255
                else:
                    r, g, b, a = 0, 0, 0, 255
                row.append((r, g, b, a))
            rows.append(row)
        
        doc.close()
        return rows, width, height
    
    @staticmethod
    def get_page_count(source: str | Path) -> int:
        """Get the number of pages in a PDF."""
        doc = fitz.open(source)
        count = len(doc)
        doc.close()
        return count
    
    @staticmethod
    def read_all_pages(source: str | Path, 
                       dpi: int = 150) -> List[Tuple[List[List[Tuple[int, int, int, int]]], int, int]]:
        """
        Read all pages from a PDF file.
        
        Args:
            source: PDF file path
            dpi: Resolution in DPI
            
        Returns:
            List of (rows, width, height) tuples, one per page
        """
        doc = fitz.open(source)
        pages = []
        
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        
        for page in doc:
            pixmap = page.get_pixmap(matrix=matrix, alpha=True)
            
            width = pixmap.width
            height = pixmap.height
            samples = pixmap.samples
            stride = pixmap.stride
            n = pixmap.n
            
            rows = []
            for y in range(height):
                row = []
                for x in range(width):
                    idx = y * stride + x * n
                    if n == 4:
                        r, g, b, a = samples[idx:idx + 4]
                    elif n == 3:
                        r, g, b = samples[idx:idx + 3]
                        a = 255
                    else:
                        r, g, b, a = 0, 0, 0, 255
                    row.append((r, g, b, a))
                rows.append(row)
            
            pages.append((rows, width, height))
        
        doc.close()
        return pages
    
    @staticmethod
    def write(dest: str | Path,
              images: List[Tuple[List[List[Tuple[int, int, int, int]]], int, int]],
              dpi: int = 150):
        """
        Create a PDF from images.
        
        Args:
            dest: Output PDF file path
            images: List of (rows, width, height) tuples
            dpi: Resolution for embedding
        """
        doc = fitz.open()  # Create new PDF
        
        for rows, width, height in images:
            # Convert rows to bytes
            samples = bytearray()
            for row in rows:
                for r, g, b, a in row:
                    samples.extend([r, g, b])
            
            # Create pixmap from samples
            pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, width, height), bytes(samples), 0)
            
            # Calculate page size in points (72 DPI)
            page_width = width * 72 / dpi
            page_height = height * 72 / dpi
            
            # Create page
            page = doc.new_page(width=page_width, height=page_height)
            
            # Insert image
            page.insert_image(fitz.Rect(0, 0, page_width, page_height), pixmap=pixmap)
        
        doc.save(dest)
        doc.close()
    
    @staticmethod
    def write_single(dest: str | Path,
                     rows: List[List[Tuple[int, int, int, int]]],
                     width: int, height: int,
                     dpi: int = 150):
        """
        Create a single-page PDF from an image.
        
        Args:
            dest: Output PDF file path
            rows: Image data
            width: Image width
            height: Image height
            dpi: Resolution for embedding
        """
        PDFHandler.write(dest, [(rows, width, height)], dpi)
