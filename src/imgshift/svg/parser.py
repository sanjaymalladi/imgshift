"""
SVG document parser.

Parses SVG XML files into a tree of Element objects.
"""

import xml.etree.ElementTree as ET
from typing import List, Tuple, Optional, Dict
from pathlib import Path
from imgshift.svg.elements import (
    Element, Rect, Circle, Ellipse, Line, Polyline, Polygon, Path,
    Style, parse_points
)
from imgshift.svg.transforms import Matrix, parse_transform


class SVGDocument:
    """Represents a parsed SVG document."""
    
    def __init__(self):
        self.width: float = 100
        self.height: float = 100
        self.viewbox: Optional[Tuple[float, float, float, float]] = None
        self.elements: List[Element] = []
        self.background: Optional[Tuple[int, int, int, int]] = None
    
    def get_size(self, target_width: Optional[int] = None, 
                 target_height: Optional[int] = None,
                 dpi: int = 96) -> Tuple[int, int]:
        """
        Calculate output size based on viewBox/dimensions and target size.
        
        Args:
            target_width: Desired output width (optional)
            target_height: Desired output height (optional)
            dpi: DPI for unit conversion
            
        Returns:
            (width, height) in pixels
        """
        # Use viewBox dimensions if available, otherwise use width/height
        if self.viewbox:
            vb_width = self.viewbox[2]
            vb_height = self.viewbox[3]
        else:
            vb_width = self.width
            vb_height = self.height
        
        # Calculate aspect ratio
        aspect = vb_width / vb_height if vb_height > 0 else 1
        
        if target_width and target_height:
            return (target_width, target_height)
        elif target_width:
            return (target_width, int(target_width / aspect))
        elif target_height:
            return (int(target_height * aspect), target_height)
        else:
            # Use default dimensions
            return (int(self.width), int(self.height))
    
    def get_transform(self, output_width: int, output_height: int) -> Matrix:
        """
        Get the transform matrix to map viewBox to output dimensions.
        
        Args:
            output_width: Target width in pixels
            output_height: Target height in pixels
            
        Returns:
            Transformation matrix
        """
        if self.viewbox:
            vb_x, vb_y, vb_width, vb_height = self.viewbox
        else:
            vb_x, vb_y = 0, 0
            vb_width, vb_height = self.width, self.height
        
        # Scale to fit
        scale_x = output_width / vb_width if vb_width > 0 else 1
        scale_y = output_height / vb_height if vb_height > 0 else 1
        
        # Translate to origin then scale
        return Matrix.translate(-vb_x, -vb_y).multiply(Matrix.scale(scale_x, scale_y))


class SVGParser:
    """Parser for SVG documents."""
    
    # SVG namespace
    SVG_NS = '{http://www.w3.org/2000/svg}'
    
    def __init__(self):
        self.doc = SVGDocument()
    
    def parse(self, source) -> SVGDocument:
        """
        Parse an SVG file or string.
        
        Args:
            source: File path (str or Path) or SVG string content
            
        Returns:
            SVGDocument with parsed elements
        """
        self.doc = SVGDocument()
        
        # Determine if source is a file path or SVG string content
        is_file = False
        file_path = None
        
        # Check if it's a path-like object (has __fspath__ method)
        if hasattr(source, '__fspath__'):
            is_file = True
            file_path = str(source)
        elif isinstance(source, str):
            # Check if it looks like XML content (starts with <)
            stripped = source.strip()
            if stripped.startswith('<'):
                # It's XML content
                is_file = False
            else:
                # Could be a file path - check if file exists
                try:
                    test_path = Path(source)
                    if test_path.exists() and test_path.is_file():
                        is_file = True
                        file_path = source
                except Exception:
                    pass
        
        # Parse XML
        if is_file and file_path:
            tree = ET.parse(file_path)
            root = tree.getroot()
        else:
            # It's XML string content
            root = ET.fromstring(source)
        
        # Parse root attributes
        self._parse_root(root)
        
        # Parse elements recursively
        self._parse_elements(root, Matrix.identity(), None)
        
        return self.doc
    
    def _parse_root(self, root: ET.Element):
        """Parse the root <svg> element attributes."""
        # Parse width/height
        width = root.get('width', '100')
        height = root.get('height', '100')
        
        self.doc.width = self._parse_length(width)
        self.doc.height = self._parse_length(height)
        
        # Parse viewBox
        viewbox = root.get('viewBox')
        if viewbox:
            parts = viewbox.replace(',', ' ').split()
            if len(parts) == 4:
                self.doc.viewbox = tuple(float(p) for p in parts)
    
    def _parse_length(self, value: str) -> float:
        """Parse a length value (e.g., '100', '100px', '10em')."""
        if not value:
            return 0
        
        value = value.strip()
        
        # Remove units and convert
        units = {'px': 1, 'pt': 1.333, 'pc': 16, 'mm': 3.779, 'cm': 37.79, 'in': 96}
        
        for unit, multiplier in units.items():
            if value.endswith(unit):
                try:
                    return float(value[:-len(unit)]) * multiplier
                except ValueError:
                    return 0
        
        # No unit or percent
        if value.endswith('%'):
            try:
                return float(value[:-1])
            except ValueError:
                return 0
        
        try:
            return float(value)
        except ValueError:
            return 0
    
    def _parse_elements(self, parent: ET.Element, parent_transform: Matrix, 
                        parent_style: Optional[Style]):
        """Recursively parse SVG elements."""
        for elem in parent:
            # Strip namespace
            tag = elem.tag.replace(self.SVG_NS, '')
            
            # Get attributes
            attrs = dict(elem.attrib)
            
            # Parse transform
            transform_str = attrs.get('transform', '')
            local_transform = parse_transform(transform_str)
            combined_transform = parent_transform.multiply(local_transform)
            
            # Parse style
            style = Style.from_attrs(attrs, parent_style)
            
            # Create element based on tag
            element = None
            
            if tag == 'rect':
                element = Rect(
                    transform=combined_transform,
                    style=style,
                    x=float(attrs.get('x', 0)),
                    y=float(attrs.get('y', 0)),
                    width=float(attrs.get('width', 0)),
                    height=float(attrs.get('height', 0)),
                    rx=float(attrs.get('rx', 0)),
                    ry=float(attrs.get('ry', 0)),
                )
            
            elif tag == 'circle':
                element = Circle(
                    transform=combined_transform,
                    style=style,
                    cx=float(attrs.get('cx', 0)),
                    cy=float(attrs.get('cy', 0)),
                    r=float(attrs.get('r', 0)),
                )
            
            elif tag == 'ellipse':
                element = Ellipse(
                    transform=combined_transform,
                    style=style,
                    cx=float(attrs.get('cx', 0)),
                    cy=float(attrs.get('cy', 0)),
                    rx=float(attrs.get('rx', 0)),
                    ry=float(attrs.get('ry', 0)),
                )
            
            elif tag == 'line':
                element = Line(
                    transform=combined_transform,
                    style=style,
                    x1=float(attrs.get('x1', 0)),
                    y1=float(attrs.get('y1', 0)),
                    x2=float(attrs.get('x2', 0)),
                    y2=float(attrs.get('y2', 0)),
                )
            
            elif tag == 'polyline':
                element = Polyline(
                    transform=combined_transform,
                    style=style,
                    points=parse_points(attrs.get('points', '')),
                )
            
            elif tag == 'polygon':
                element = Polygon(
                    transform=combined_transform,
                    style=style,
                    points=parse_points(attrs.get('points', '')),
                )
            
            elif tag == 'path':
                element = Path(
                    transform=combined_transform,
                    style=style,
                    d=attrs.get('d', ''),
                )
            
            elif tag in ('g', 'svg', 'defs', 'symbol', 'use'):
                # Container elements - recurse into children
                self._parse_elements(elem, combined_transform, style)
                continue
            
            if element:
                self.doc.elements.append(element)
            
            # Recurse for any children (some elements can contain others)
            self._parse_elements(elem, combined_transform, style)
