"""
Tests for SVG path parser.
"""

import pytest
from imgshift.svg.path_parser import parse_path, path_to_points, cubic_bezier, quadratic_bezier


class TestParsePath:
    """Test SVG path parsing."""
    
    def test_moveto_absolute(self):
        """Test M command."""
        commands = parse_path("M 10 20")
        assert len(commands) == 1
        assert commands[0].command == 'M'
        assert commands[0].args == (10.0, 20.0)
    
    def test_moveto_relative(self):
        """Test m command."""
        commands = parse_path("m 10 20")
        assert len(commands) == 1
        assert commands[0].command == 'm'
        assert commands[0].args == (10.0, 20.0)
    
    def test_lineto(self):
        """Test L command."""
        commands = parse_path("M 0 0 L 100 100")
        assert len(commands) == 2
        assert commands[1].command == 'L'
        assert commands[1].args == (100.0, 100.0)
    
    def test_horizontal_lineto(self):
        """Test H command."""
        commands = parse_path("M 0 0 H 50")
        assert len(commands) == 2
        assert commands[1].command == 'H'
        assert commands[1].args == (50.0,)
    
    def test_vertical_lineto(self):
        """Test V command."""
        commands = parse_path("M 0 0 V 50")
        assert len(commands) == 2
        assert commands[1].command == 'V'
        assert commands[1].args == (50.0,)
    
    def test_closepath(self):
        """Test Z command."""
        commands = parse_path("M 0 0 L 10 0 L 10 10 Z")
        assert len(commands) == 4
        assert commands[3].command == 'Z'
        assert commands[3].args == ()
    
    def test_cubic_bezier(self):
        """Test C command."""
        commands = parse_path("M 0 0 C 10 20 30 40 50 60")
        assert len(commands) == 2
        assert commands[1].command == 'C'
        assert commands[1].args == (10.0, 20.0, 30.0, 40.0, 50.0, 60.0)
    
    def test_quadratic_bezier(self):
        """Test Q command."""
        commands = parse_path("M 0 0 Q 10 20 30 40")
        assert len(commands) == 2
        assert commands[1].command == 'Q'
        assert commands[1].args == (10.0, 20.0, 30.0, 40.0)
    
    def test_arc(self):
        """Test A command."""
        commands = parse_path("M 0 0 A 25 25 0 1 1 50 0")
        assert len(commands) == 2
        assert commands[1].command == 'A'
        assert commands[1].args == (25.0, 25.0, 0.0, 1.0, 1.0, 50.0, 0.0)
    
    def test_complex_path(self):
        """Test a complex path."""
        d = "M 10,30 A 20,20 0,0,1 50,30 A 20,20 0,0,1 90,30 Q 90,60 50,90 Q 10,60 10,30 z"
        commands = parse_path(d)
        assert len(commands) == 6
        assert commands[0].command == 'M'
        assert commands[1].command == 'A'
        assert commands[2].command == 'A'
        assert commands[3].command == 'Q'
        assert commands[4].command == 'Q'
        assert commands[5].command == 'z'
    
    def test_consecutive_moveto_becomes_lineto(self):
        """Test that consecutive coords after M become L."""
        commands = parse_path("M 0 0 10 10 20 20")
        assert len(commands) == 3
        assert commands[0].command == 'M'
        assert commands[1].command == 'L'
        assert commands[2].command == 'L'


class TestPathToPoints:
    """Test path to points conversion."""
    
    def test_simple_triangle(self):
        """Test converting a simple triangle path."""
        commands = parse_path("M 0 0 L 100 0 L 50 100 Z")
        subpaths = path_to_points(commands)
        
        assert len(subpaths) == 1
        # Should have 4 points (3 corners + close)
        assert len(subpaths[0]) == 4
        assert subpaths[0][0] == (0.0, 0.0)
        assert subpaths[0][1] == (100.0, 0.0)
        assert subpaths[0][2] == (50.0, 100.0)
        assert subpaths[0][3] == (0.0, 0.0)  # Close back to start
    
    def test_relative_coords(self):
        """Test relative coordinates."""
        commands = parse_path("M 10 10 l 20 0 l 0 20 z")
        subpaths = path_to_points(commands)
        
        assert len(subpaths) == 1
        assert subpaths[0][0] == (10.0, 10.0)
        assert subpaths[0][1] == (30.0, 10.0)  # 10 + 20
        assert subpaths[0][2] == (30.0, 30.0)  # 10 + 20


class TestBezierCurves:
    """Test bezier curve generation."""
    
    def test_cubic_bezier_endpoints(self):
        """Test that cubic bezier starts and ends at correct points."""
        points = cubic_bezier(0, 0, 10, 20, 30, 20, 40, 0, segments=10)
        
        assert points[0] == (0, 0)
        assert points[-1] == (40, 0)
    
    def test_quadratic_bezier_endpoints(self):
        """Test that quadratic bezier starts and ends at correct points."""
        points = quadratic_bezier(0, 0, 20, 40, 40, 0, segments=10)
        
        assert points[0] == (0, 0)
        assert points[-1] == (40, 0)
