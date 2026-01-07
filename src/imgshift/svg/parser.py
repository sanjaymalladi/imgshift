"""
SVG document parser.

Parses SVG XML files into a tree of Element objects.
"""

import xml.etree.ElementTree as ET
from typing import List, Tuple, Optional, Dict
from pathlib import Path
from imgshift.svg.elements import (
    Element, Rect, Circle, Ellipse, Line, Polyline, Polygon, Path, Text,
    Style, parse_points
)
from imgshift.svg.paint import GradientStop, LinearGradient, RadialGradient
from imgshift.utils import parse_color

from imgshift.svg.transforms import Matrix, parse_transform


class SVGDocument:
    """Represents a parsed SVG document."""
    
    def __init__(self):
        self.width: float = 100
        self.height: float = 100
        self.viewbox: Optional[Tuple[float, float, float, float]] = None
        self.elements: List[Element] = []
        self.background: Optional[Tuple[int, int, int, int]] = None
        self.defs: Dict[str, Any] = {}  # ID -> Paint/Element mapping
    
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
    
    def _parse_stops(self, elem: ET.Element) -> List[GradientStop]:
        """Parse gradient stops."""
        stops = []
        for stop in elem:
            tag = stop.tag.replace(self.SVG_NS, '')
            if tag == 'stop':
                attrs = dict(stop.attrib)
                
                # Parse offset
                offset_str = attrs.get('offset', '0').strip()
                if offset_str.endswith('%'):
                    offset = float(offset_str[:-1]) / 100.0
                else:
                    offset = float(offset_str)
                
                # Parse color
                color_str = attrs.get('stop-color')
                style_str = attrs.get('style', '')
                
                # Style overrides attribute
                if style_str:
                    for item in style_str.split(';'):
                        if ':' in item:
                            k, v = item.split(':', 1)
                            if k.strip() == 'stop-color':
                                color_str = v.strip()
                
                if color_str:
                    r, g, b, a = parse_color(color_str)
                    
                    # Apply stop-opacity
                    opacity = attrs.get('stop-opacity', '1')
                    if style_str:
                         for item in style_str.split(';'):
                            if ':' in item:
                                k, v = item.split(':', 1)
                                if k.strip() == 'stop-opacity':
                                    opacity = v.strip()
                    
                    try:
                        a = int(a * float(opacity))
                    except ValueError:
                        pass
                    
                    stops.append(GradientStop(offset, (r, g, b, a)))
        return stops

    def _parse_linear_gradient(self, elem: ET.Element, attrs: Dict[str, str]):
        """Parse linear gradient and store in defs."""
        gid = attrs.get('id')
        if not gid:
            return
            
        x1 = self._parse_length(attrs.get('x1', '0%'))
        y1 = self._parse_length(attrs.get('y1', '0%'))
        x2 = self._parse_length(attrs.get('x2', '100%'))
        y2 = self._parse_length(attrs.get('y2', '0%'))
        
        stops = self._parse_stops(elem)
        
        # Handle gradientTransform
        transform = Matrix.identity()
        if 'gradientTransform' in attrs:
            transform = parse_transform(attrs['gradientTransform'])
            
        units = attrs.get('gradientUnits', 'objectBoundingBox')
            
        gradient = LinearGradient(x1, y1, x2, y2, stops, transform=transform, units=units)
        self.doc.defs[gid] = gradient

    def _parse_radial_gradient(self, elem: ET.Element, attrs: Dict[str, str]):
        """Parse radial gradient and store in defs."""
        gid = attrs.get('id')
        if not gid:
            return
            
        cx = self._parse_length(attrs.get('cx', '50%'))
        cy = self._parse_length(attrs.get('cy', '50%'))
        r = self._parse_length(attrs.get('r', '50%'))
        fx = self._parse_length(attrs.get('fx', str(cx)))
        fy = self._parse_length(attrs.get('fy', str(cy)))
        
        stops = self._parse_stops(elem)
        
        # Handle gradientTransform
        transform = Matrix.identity()
        if 'gradientTransform' in attrs:
            transform = parse_transform(attrs['gradientTransform'])
            
        units = attrs.get('gradientUnits', 'objectBoundingBox')
            
        gradient = RadialGradient(cx, cy, r, fx, fy, stops, transform=transform, units=units)
        self.doc.defs[gid] = gradient

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
            
            if tag == 'linearGradient':
                self._parse_linear_gradient(elem, attrs)
                continue
            
            elif tag == 'radialGradient':
                self._parse_radial_gradient(elem, attrs)
                continue
                
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
            
            elif tag == 'text':
                element = Text(
                    transform=combined_transform,
                    style=style,
                    x=float(attrs.get('x', 0)),
                    y=float(attrs.get('y', 0)),
                    text=elem.text or "",
                    font_family=attrs.get('font-family', 'sans-serif'),
                    font_size=attrs.get('font-size', '12'),
                )
            
            elif tag in ('g', 'svg', 'defs', 'symbol', 'use'):
                # Container elements - recurse into children
                self._parse_elements(elem, combined_transform, style)
                continue
            
            if element:
                self.doc.elements.append(element)
            
            # Recurse for any children (some elements can contain others)
            self._parse_elements(elem, combined_transform, style)
