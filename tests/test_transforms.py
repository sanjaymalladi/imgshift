"""
Tests for SVG transforms.
"""

import pytest
import math
from imgshift.svg.transforms import Matrix, parse_transform


class TestMatrix:
    """Test Matrix operations."""
    
    def test_identity(self):
        """Test identity matrix."""
        m = Matrix.identity()
        x, y = m.transform_point(10, 20)
        assert x == 10
        assert y == 20
    
    def test_translate(self):
        """Test translation matrix."""
        m = Matrix.translate(5, 10)
        x, y = m.transform_point(10, 20)
        assert x == 15
        assert y == 30
    
    def test_scale(self):
        """Test scale matrix."""
        m = Matrix.scale(2, 3)
        x, y = m.transform_point(10, 20)
        assert x == 20
        assert y == 60
    
    def test_scale_uniform(self):
        """Test uniform scale."""
        m = Matrix.scale(2)
        x, y = m.transform_point(10, 20)
        assert x == 20
        assert y == 40
    
    def test_rotate_90(self):
        """Test 90 degree rotation."""
        m = Matrix.rotate(90)
        x, y = m.transform_point(10, 0)
        assert abs(x - 0) < 0.001
        assert abs(y - 10) < 0.001
    
    def test_rotate_180(self):
        """Test 180 degree rotation."""
        m = Matrix.rotate(180)
        x, y = m.transform_point(10, 20)
        assert abs(x - (-10)) < 0.001
        assert abs(y - (-20)) < 0.001
    
    def test_multiply(self):
        """Test matrix multiplication."""
        # Translate then scale
        t = Matrix.translate(10, 10)
        s = Matrix.scale(2, 2)
        combined = t.multiply(s)
        
        x, y = combined.transform_point(5, 5)
        # First translate: (5, 5) -> (15, 15)
        # Then scale: (15, 15) -> (30, 30)
        assert x == 30
        assert y == 30


class TestParseTransform:
    """Test transform string parsing."""
    
    def test_parse_translate(self):
        """Test parsing translate()."""
        m = parse_transform("translate(10, 20)")
        x, y = m.transform_point(0, 0)
        assert x == 10
        assert y == 20
    
    def test_parse_translate_single_arg(self):
        """Test translate with single argument."""
        m = parse_transform("translate(10)")
        x, y = m.transform_point(0, 0)
        assert x == 10
        assert y == 0
    
    def test_parse_scale(self):
        """Test parsing scale()."""
        m = parse_transform("scale(2, 3)")
        x, y = m.transform_point(10, 10)
        assert x == 20
        assert y == 30
    
    def test_parse_rotate(self):
        """Test parsing rotate()."""
        m = parse_transform("rotate(90)")
        x, y = m.transform_point(10, 0)
        assert abs(x) < 0.001
        assert abs(y - 10) < 0.001
    
    def test_parse_multiple_transforms(self):
        """Test parsing multiple transforms."""
        m = parse_transform("translate(10, 0) scale(2)")
        x, y = m.transform_point(5, 5)
        # translate: (5, 5) -> (15, 5)
        # scale: (15, 5) -> (30, 10)
        assert x == 30
        assert y == 10
    
    def test_parse_matrix(self):
        """Test parsing matrix()."""
        m = parse_transform("matrix(1, 0, 0, 1, 10, 20)")
        x, y = m.transform_point(0, 0)
        assert x == 10
        assert y == 20
    
    def test_parse_empty(self):
        """Test parsing empty string."""
        m = parse_transform("")
        x, y = m.transform_point(10, 20)
        assert x == 10
        assert y == 20
