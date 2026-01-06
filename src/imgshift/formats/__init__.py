"""
Format handlers module.
"""

from imgshift.formats.png import PNGHandler
from imgshift.formats.jpeg import JPEGHandler
from imgshift.formats.pdf import PDFHandler

__all__ = ["PNGHandler", "JPEGHandler", "PDFHandler"]
