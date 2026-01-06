"""
SVG element classes representing shapes and paths.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from imgshift.svg.transforms import Matrix, parse_transform
from imgshift.svg.path_parser import parse_path, path_to_points
from imgshift.utils import parse_color
import math


@dataclass
class Style:
    """SVG styling properties."""
    fill: Tuple[int, int, int, int] = (0, 0, 0, 255)  # RGBA
    stroke: Tuple[int, int, int, int] = (0, 0, 0, 0)  # RGBA (transparent by default)
    stroke_width: float = 1.0
    opacity: float = 1.0
    fill_opacity: float = 1.0
    stroke_opacity: float = 1.0
    
    @classmethod
    def from_attrs(cls, attrs: Dict[str, str], parent_style: Optional['Style'] = None) -> 'Style':
        """Create Style from SVG attributes, inheriting from parent if provided."""
        style = cls()
        
        # Inherit from parent
        if parent_style:
            style.fill = parent_style.fill
            style.stroke = parent_style.stroke
            style.stroke_width = parent_style.stroke_width
            style.opacity = parent_style.opacity
            style.fill_opacity = parent_style.fill_opacity
            style.stroke_opacity = parent_style.stroke_opacity
        
        # Parse style attribute
        style_str = attrs.get('style', '')
        style_attrs = {}
        for item in style_str.split(';'):
            if ':' in item:
                key, value = item.split(':', 1)
                style_attrs[key.strip()] = value.strip()
        
        # Merge direct attributes with style attribute (direct takes precedence)
        all_attrs = {**style_attrs}
        for key in ['fill', 'stroke', 'stroke-width', 'opacity', 'fill-opacity', 'stroke-opacity']:
            if key in attrs:
                all_attrs[key] = attrs[key]
        
        # Apply attributes
        if 'fill' in all_attrs:
            style.fill = parse_color(all_attrs['fill'])
        
        if 'stroke' in all_attrs:
            style.stroke = parse_color(all_attrs['stroke'])
        
        if 'stroke-width' in all_attrs:
            try:
                style.stroke_width = float(all_attrs['stroke-width'].replace('px', ''))
            except ValueError:
                pass
        
        if 'opacity' in all_attrs:
            try:
                style.opacity = float(all_attrs['opacity'])
            except ValueError:
                pass
        
        if 'fill-opacity' in all_attrs:
            try:
                style.fill_opacity = float(all_attrs['fill-opacity'])
            except ValueError:
                pass
        
        if 'stroke-opacity' in all_attrs:
            try:
                style.stroke_opacity = float(all_attrs['stroke-opacity'])
            except ValueError:
                pass
        
        return style
    
    def get_fill_color(self) -> Tuple[int, int, int, int]:
        """Get fill color with opacity applied."""
        r, g, b, a = self.fill
        final_alpha = int(a * self.opacity * self.fill_opacity)
        return (r, g, b, final_alpha)
    
    def get_stroke_color(self) -> Tuple[int, int, int, int]:
        """Get stroke color with opacity applied."""
        r, g, b, a = self.stroke
        final_alpha = int(a * self.opacity * self.stroke_opacity)
        return (r, g, b, final_alpha)


@dataclass
class Element:
    """Base class for SVG elements."""
    transform: Matrix = field(default_factory=Matrix.identity)
    style: Style = field(default_factory=Style)
    
    def get_polygons(self) -> List[List[Tuple[float, float]]]:
        """
        Get the element as a list of polygons (subpaths).
        Each polygon is a list of (x, y) points with transform applied.
        
        Returns:
            List of polygons
        """
        raise NotImplementedError
    
    def apply_transform(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Apply the element's transform to a list of points."""
        return [self.transform.transform_point(x, y) for x, y in points]


@dataclass
class Rect(Element):
    """SVG rect element."""
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0
    rx: float = 0
    ry: float = 0
    
    def get_polygons(self) -> List[List[Tuple[float, float]]]:
        if self.rx > 0 or self.ry > 0:
            # Rounded rectangle
            return self._rounded_rect()
        
        # Simple rectangle
        points = [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height),
            (self.x, self.y),  # Close
        ]
        return [self.apply_transform(points)]
    
    def _rounded_rect(self) -> List[List[Tuple[float, float]]]:
        """Generate points for a rounded rectangle."""
        rx = min(self.rx, self.width / 2)
        ry = min(self.ry if self.ry > 0 else rx, self.height / 2)
        
        points = []
        segments = 8
        
        # Top edge
        points.append((self.x + rx, self.y))
        points.append((self.x + self.width - rx, self.y))
        
        # Top-right corner
        for i in range(segments + 1):
            angle = -math.pi / 2 + (math.pi / 2) * (i / segments)
            px = self.x + self.width - rx + rx * math.cos(angle)
            py = self.y + ry + ry * math.sin(angle)
            points.append((px, py))
        
        # Right edge
        points.append((self.x + self.width, self.y + self.height - ry))
        
        # Bottom-right corner
        for i in range(segments + 1):
            angle = (math.pi / 2) * (i / segments)
            px = self.x + self.width - rx + rx * math.cos(angle)
            py = self.y + self.height - ry + ry * math.sin(angle)
            points.append((px, py))
        
        # Bottom edge
        points.append((self.x + rx, self.y + self.height))
        
        # Bottom-left corner
        for i in range(segments + 1):
            angle = math.pi / 2 + (math.pi / 2) * (i / segments)
            px = self.x + rx + rx * math.cos(angle)
            py = self.y + self.height - ry + ry * math.sin(angle)
            points.append((px, py))
        
        # Left edge
        points.append((self.x, self.y + ry))
        
        # Top-left corner
        for i in range(segments + 1):
            angle = math.pi + (math.pi / 2) * (i / segments)
            px = self.x + rx + rx * math.cos(angle)
            py = self.y + ry + ry * math.sin(angle)
            points.append((px, py))
        
        # Close
        points.append(points[0])
        
        return [self.apply_transform(points)]


@dataclass
class Circle(Element):
    """SVG circle element."""
    cx: float = 0
    cy: float = 0
    r: float = 0
    
    def get_polygons(self) -> List[List[Tuple[float, float]]]:
        segments = max(32, int(self.r * 2))
        points = []
        
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = self.cx + self.r * math.cos(angle)
            y = self.cy + self.r * math.sin(angle)
            points.append((x, y))
        
        points.append(points[0])  # Close
        return [self.apply_transform(points)]


@dataclass
class Ellipse(Element):
    """SVG ellipse element."""
    cx: float = 0
    cy: float = 0
    rx: float = 0
    ry: float = 0
    
    def get_polygons(self) -> List[List[Tuple[float, float]]]:
        segments = max(32, int(max(self.rx, self.ry) * 2))
        points = []
        
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = self.cx + self.rx * math.cos(angle)
            y = self.cy + self.ry * math.sin(angle)
            points.append((x, y))
        
        points.append(points[0])  # Close
        return [self.apply_transform(points)]


@dataclass
class Line(Element):
    """SVG line element."""
    x1: float = 0
    y1: float = 0
    x2: float = 0
    y2: float = 0
    
    def get_polygons(self) -> List[List[Tuple[float, float]]]:
        points = [(self.x1, self.y1), (self.x2, self.y2)]
        return [self.apply_transform(points)]


@dataclass
class Polyline(Element):
    """SVG polyline element."""
    points: List[Tuple[float, float]] = field(default_factory=list)
    
    def get_polygons(self) -> List[List[Tuple[float, float]]]:
        if not self.points:
            return []
        return [self.apply_transform(self.points)]


@dataclass
class Polygon(Element):
    """SVG polygon element."""
    points: List[Tuple[float, float]] = field(default_factory=list)
    
    def get_polygons(self) -> List[List[Tuple[float, float]]]:
        if not self.points:
            return []
        pts = list(self.points)
        if pts and pts[0] != pts[-1]:
            pts.append(pts[0])  # Close
        return [self.apply_transform(pts)]


@dataclass
class Path(Element):
    """SVG path element."""
    d: str = ""
    
    def get_polygons(self) -> List[List[Tuple[float, float]]]:
        commands = parse_path(self.d)
        subpaths = path_to_points(commands)
        return [self.apply_transform(pts) for pts in subpaths]


def parse_points(points_str: str) -> List[Tuple[float, float]]:
    """Parse SVG points attribute into a list of (x, y) tuples."""
    if not points_str:
        return []
    
    # Split by comma or whitespace
    import re
    values = [float(x) for x in re.split(r'[\s,]+', points_str.strip()) if x]
    
    # Pair up values
    points = []
    for i in range(0, len(values) - 1, 2):
        points.append((values[i], values[i + 1]))
    
    return points
