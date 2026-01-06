"""
Tests for core conversion functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path

from imgshift.core import convert, Image, _resize
from imgshift.svg.parser import SVGParser
from imgshift.svg.rasterizer import Rasterizer


class TestSVGRendering:
    """Test SVG parsing and rendering."""
    
    def test_parse_simple_rect(self):
        """Test parsing a simple rect SVG."""
        svg = '''<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
            <rect x="10" y="10" width="80" height="80" fill="red"/>
        </svg>'''
        
        parser = SVGParser()
        doc = parser.parse(svg)
        
        assert doc.width == 100
        assert doc.height == 100
        assert len(doc.elements) == 1
    
    def test_parse_circle(self):
        """Test parsing a circle."""
        svg = '''<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="40" fill="blue"/>
        </svg>'''
        
        parser = SVGParser()
        doc = parser.parse(svg)
        
        assert len(doc.elements) == 1
    
    def test_render_svg(self):
        """Test rendering SVG to pixel buffer."""
        svg = '''<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="100" height="100" fill="red"/>
        </svg>'''
        
        parser = SVGParser()
        doc = parser.parse(svg)
        
        rasterizer = Rasterizer()
        buffer = rasterizer.render(doc, 100, 100)
        
        assert buffer.width == 100
        assert buffer.height == 100
    
    def test_render_with_transform(self):
        """Test rendering with transform."""
        svg = '''<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="50" height="50" fill="blue" transform="translate(25, 25)"/>
        </svg>'''
        
        parser = SVGParser()
        doc = parser.parse(svg)
        
        rasterizer = Rasterizer()
        buffer = rasterizer.render(doc, 100, 100)
        
        assert buffer.width == 100
        assert buffer.height == 100


class TestResize:
    """Test image resize function."""
    
    def test_resize_width_only(self):
        """Test resizing by width only."""
        # Create a 100x50 image
        rows = [[(255, 0, 0, 255)] * 100 for _ in range(50)]
        
        new_rows, new_w, new_h = _resize(rows, 100, 50, 50, None)
        
        assert new_w == 50
        assert new_h == 25  # Maintains aspect ratio
    
    def test_resize_height_only(self):
        """Test resizing by height only."""
        rows = [[(0, 255, 0, 255)] * 100 for _ in range(50)]
        
        new_rows, new_w, new_h = _resize(rows, 100, 50, None, 100)
        
        assert new_h == 100
        assert new_w == 200  # Maintains aspect ratio
    
    def test_resize_both(self):
        """Test resizing with both width and height."""
        rows = [[(0, 0, 255, 255)] * 100 for _ in range(100)]
        
        new_rows, new_w, new_h = _resize(rows, 100, 100, 50, 25)
        
        assert new_w == 50
        assert new_h == 25


class TestConvert:
    """Test conversion functions."""
    
    def test_svg_to_png(self):
        """Test converting SVG to PNG."""
        svg_content = '''<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
            <rect x="10" y="10" width="80" height="80" fill="#ff0000"/>
        </svg>'''
        
        with tempfile.TemporaryDirectory() as tmpdir:
            svg_path = Path(tmpdir) / "test.svg"
            png_path = Path(tmpdir) / "test.png"
            
            svg_path.write_text(svg_content)
            
            convert(svg_path, png_path)
            
            assert png_path.exists()
            assert png_path.stat().st_size > 0


class TestImageClass:
    """Test the Image fluent API."""
    
    def test_image_chain(self):
        """Test method chaining."""
        svg_content = '''<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="40" fill="green"/>
        </svg>'''
        
        with tempfile.TemporaryDirectory() as tmpdir:
            svg_path = Path(tmpdir) / "test.svg"
            png_path = Path(tmpdir) / "test.png"
            
            svg_path.write_text(svg_content)
            
            Image(svg_path).resize(200, 200).save(png_path)
            
            assert png_path.exists()
