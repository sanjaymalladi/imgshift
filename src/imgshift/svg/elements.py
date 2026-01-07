"""
SVG element classes representing shapes and paths.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from imgshift.svg.transforms import Matrix, parse_transform
from imgshift.svg.path_parser import parse_path, path_to_points
from imgshift.svg.paint import Paint, SolidColor, Gradient
from imgshift.utils import parse_color
import math
import re

@dataclass
class Style:
    """SVG styling properties."""
    # fill/stroke can be Paint object (SolidColor, Gradient) or str (url ref)
    fill: Any = field(default_factory=lambda: SolidColor((0, 0, 0, 255)))
    stroke: Any = field(default_factory=lambda: SolidColor((0, 0, 0, 0)))
    stroke_width: float = 1.0
    opacity: float = 1.0
    fill_opacity: float = 1.0
    stroke_opacity: float = 1.0
    fill_rule: str = 'nonzero'  # nonzero (default) or evenodd
    
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
            style.fill_rule = parent_style.fill_rule
        
        # Parse style attribute
        style_str = attrs.get('style', '')
        style_attrs = {}
        for item in style_str.split(';'):
            if ':' in item:
                key, value = item.split(':', 1)
                style_attrs[key.strip()] = value.strip()
        
        # Merge direct attributes with style attribute
        all_attrs = {}
        for key in ['fill', 'stroke', 'stroke-width', 'opacity', 'fill-opacity', 'stroke-opacity', 'fill-rule']:
            if key in attrs:
                all_attrs[key] = attrs[key]
        
        all_attrs.update(style_attrs)
        
        # Apply attributes
        if 'fill' in all_attrs:
            val = all_attrs['fill'].strip()
            if val.startswith('url('):
                style.fill = val
            else:
                style.fill = SolidColor(parse_color(val))
        
        if 'stroke' in all_attrs:
            val = all_attrs['stroke'].strip()
            if val.startswith('url('):
                style.stroke = val
            else:
                style.stroke = SolidColor(parse_color(val))
        
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

        if 'fill-rule' in all_attrs:
            style.fill_rule = all_attrs['fill-rule'].strip().lower()
        
        return style


@dataclass
class Element:
    """Base class for SVG nodes."""
    id: Optional[str] = None
    style: Style = field(default_factory=Style)
    transform: Matrix = field(default_factory=Matrix.identity)
    
    def apply_transform(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Apply local transform to points."""
        return [self.transform.transform_point(x, y) for x, y in points]
    
    def get_bbox(self) -> Tuple[float, float, float, float]:
        """
        Get bounding box (min_x, min_y, width, height) in local user space.
        """
        return (0, 0, 0, 0)


@dataclass
class Path(Element):
    """Path element (<path d="...">)."""
    d: str = ""
    
    def to_polygons(self) -> List[Tuple[List[Tuple[float, float]], int]]:
        """Convert path to polygons with winding direction."""
        commands = parse_path(self.d)
        return path_to_points(commands)
        
    def get_bbox(self) -> Tuple[float, float, float, float]:
        polys = self.to_polygons()
        if not polys:
            return (0, 0, 0, 0)
        
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        
        found = False
        for poly, _ in polys:  # Unpack (polygon, direction) tuple
            for x, y in poly:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
                found = True
        
        if not found:
            return (0, 0, 0, 0)
            
        return (min_x, min_y, max_x - min_x, max_y - min_y)


@dataclass
class Rect(Element):
    """Rectangle element (<rect>)."""
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0
    rx: float = 0
    ry: float = 0
    
    def to_polygons(self) -> List[Tuple[List[Tuple[float, float]], int]]:
        if self.rx > 0 or self.ry > 0:
            return [(self.apply_transform(points), 1) for points in self._rounded_rect()]
            
        points = [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height),
            (self.x, self.y),  # Close
        ]
        return [(self.apply_transform(points), 1)]
    
    def _rounded_rect(self) -> List[List[Tuple[float, float]]]:
        """Generate points for a rounded rectangle."""
        rx = min(self.rx, self.width / 2)
        ry = min(self.ry if self.ry > 0 else rx, self.height / 2)
        
        points = []
        segments = 8
        
        # Top right
        points.append((self.x + self.width - rx, self.y))
        for i in range(segments + 1):
            angle = -math.pi/2 + (math.pi/2) * (i/segments)
            points.append((
                self.x + self.width - rx + rx * math.cos(angle),
                self.y + ry + ry * math.sin(angle)
            ))
            
        # Bottom right
        points.append((self.x + self.width, self.y + self.height - ry))
        for i in range(segments + 1):
            angle = (math.pi/2) * (i/segments)
            points.append((
                self.x + self.width - rx + rx * math.cos(angle),
                self.y + self.height - ry + ry * math.sin(angle)
            ))
            
        # Bottom left
        points.append((self.x + rx, self.y + self.height))
        for i in range(segments + 1):
            angle = math.pi/2 + (math.pi/2) * (i/segments)
            points.append((
                self.x + rx + rx * math.cos(angle),
                self.y + self.height - ry + ry * math.sin(angle)
            ))
            
        # Top left
        points.append((self.x, self.y + ry))
        for i in range(segments + 1):
            angle = math.pi + (math.pi/2) * (i/segments)
            points.append((
                self.x + rx + rx * math.cos(angle),
                self.y + ry + ry * math.sin(angle)
            ))
            
        points.append(points[0])
        return [points]

    def get_bbox(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.width, self.height)


@dataclass
class Circle(Element):
    """Circle element (<circle>)."""
    cx: float = 0
    cy: float = 0
    r: float = 0
    
    def to_polygons(self) -> List[Tuple[List[Tuple[float, float]], int]]:
        points = []
        segments = max(16, int(self.r * 2))  # Adaptive segments
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            px = self.cx + self.r * math.cos(angle)
            py = self.cy + self.r * math.sin(angle)
            points.append((px, py))
        points.append(points[0])
        return [(self.apply_transform(points), 1)]

    def get_bbox(self) -> Tuple[float, float, float, float]:
        return (self.cx - self.r, self.cy - self.r, self.r * 2, self.r * 2)


@dataclass
class Ellipse(Element):
    """Ellipse element (<ellipse>)."""
    cx: float = 0
    cy: float = 0
    rx: float = 0
    ry: float = 0
    
    def to_polygons(self) -> List[Tuple[List[Tuple[float, float]], int]]:
        points = []
        segments = max(16, int(max(self.rx, self.ry) * 2))
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            px = self.cx + self.rx * math.cos(angle)
            py = self.cy + self.ry * math.sin(angle)
            points.append((px, py))
        points.append(points[0])
        return [(self.apply_transform(points), 1)]

    def get_bbox(self) -> Tuple[float, float, float, float]:
        return (self.cx - self.rx, self.cy - self.ry, self.rx * 2, self.ry * 2)


@dataclass
class Line(Element):
    """Line element (<line>)."""
    x1: float = 0
    y1: float = 0
    x2: float = 0
    y2: float = 0
    
    def to_polygons(self) -> List[Tuple[List[Tuple[float, float]], int]]:
        return [(self.apply_transform([(self.x1, self.y1), (self.x2, self.y2)]), 1)]

    def get_bbox(self) -> Tuple[float, float, float, float]:
        return (min(self.x1, self.x2), min(self.y1, self.y2), abs(self.x2-self.x1), abs(self.y2-self.y1))


@dataclass
class Polyline(Element):
    """Polyline element (<polyline>)."""
    points: List[Tuple[float, float]] = field(default_factory=list)
    
    def to_polygons(self) -> List[Tuple[List[Tuple[float, float]], int]]:
        if not self.points: return []
        return [(self.apply_transform(self.points), 1)]

    def get_bbox(self) -> Tuple[float, float, float, float]:
        if not self.points: return (0,0,0,0)
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys))


@dataclass
class Polygon(Element):
    """Polygon element (<polygon>)."""
    points: List[Tuple[float, float]] = field(default_factory=list)
    
    def to_polygons(self) -> List[Tuple[List[Tuple[float, float]], int]]:
        if not self.points: return []
        pts = list(self.points)
        if pts and pts[0] != pts[-1]:
            pts.append(pts[0])
        return [(self.apply_transform(pts), 1)]

    def get_bbox(self) -> Tuple[float, float, float, float]:
        if not self.points: return (0,0,0,0)
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys))


@dataclass
class Group(Element):
    """Group element (<g>)."""
    children: List[Element] = field(default_factory=list)
    
    def get_polygons(self) -> List[List[Tuple[float, float]]]:
        return []
        
    def get_bbox(self) -> Tuple[float, float, float, float]:
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        found = False
        
        for child in self.children:
             cx, cy, cw, ch = child.get_bbox()
             if cw == 0 and ch == 0: continue
             
             # Transform corners to group space
             corners = [
                 (cx, cy), (cx+cw, cy),
                 (cx+cw, cy+ch), (cx, cy+ch)
             ]
             
             # Apply child's transform (which is relative to group)
             t_corners = child.apply_transform(corners)
             
             for tx, ty in t_corners:
                 min_x = min(min_x, tx)
                 min_y = min(min_y, ty)
                 max_x = max(max_x, tx)
                 max_y = max(max_y, ty)
                 found = True
                 
        if not found:
            return (0, 0, 0, 0)
        return (min_x, min_y, max_x - min_x, max_y - min_y)


@dataclass
class Text(Element):
    """Text element (<text>)."""
    x: float = 0
    y: float = 0
    text: str = ""
    font_family: str = "Arial"
    font_size: float = 12
    
    def get_polygons(self) -> List[List[Tuple[float, float]]]:
        return []
        
    def get_bbox(self) -> Tuple[float, float, float, float]:
        # Approximate
        width = len(self.text) * self.font_size * 0.6
        height = self.font_size
        return (self.x, self.y - height, width, height)

def parse_points(points_str: str) -> List[Tuple[float, float]]:
    """Parse SVG points attribute into a list of (x, y) tuples."""
    if not points_str:
        return []
    values = [float(x) for x in re.split(r'[\s,]+', points_str.strip()) if x]
    points = []
    for i in range(0, len(values) - 1, 2):
        points.append((values[i], values[i + 1]))
    return points
