"""
Geometry utilities for SVG rendering.

Handles vector math and path manipulations (stroking, offsetting).
"""

import math
from typing import List, Tuple

Point = Tuple[float, float]
Polygon = List[Point]

def distance(p1: Point, p2: Point) -> float:
    """Euclidean distance between two points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def normalize(v: Point) -> Point:
    """Normalize a vector."""
    l = math.hypot(v[0], v[1])
    if l == 0:
        return (0, 0)
    return (v[0]/l, v[1]/l)

def stroke_polyline(points: List[Point], width: float, 
                   cap: str = 'butt', join: str = 'miter') -> List[Tuple[Polygon, int]]:
    """
    Convert a polyline (list of points) into a list of closed polygons representing the stroke.
    
    Generates quads for segments and circles/fans for joins/caps.
    Returns list of (polygon, direction) tuples - all strokes are clockwise (+1).
    """
    if len(points) < 2:
        return []
        
    polygons = []
    half_width = width / 2.0
    
    # Process segments
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.hypot(dx, dy)
        
        if length == 0:
            continue
            
        # Normal vector (perpendicular)
        nx = -dy / length
        ny = dx / length
        
        # Offset points
        ox = nx * half_width
        oy = ny * half_width
        
        # Segment Quad
        quad = [
            (p1[0] + ox, p1[1] + oy),
            (p2[0] + ox, p2[1] + oy),
            (p2[0] - ox, p2[1] - oy),
            (p1[0] - ox, p1[1] - oy)
        ]
        polygons.append((quad, 1))  # Clockwise winding
        
        # Start Cap (only for first segment)
        if i == 0 and cap == 'round':
            polygons.append((_create_round_cap(p1, nx, ny, half_width), 1))
        elif i == 0 and cap == 'square':
             polygons.append((_create_square_cap(p1, nx, ny, half_width, -1), 1))

        # End Cap (only for last segment)
        if i == len(points) - 2 and cap == 'round':
            polygons.append((_create_round_cap(p2, nx, ny, half_width), 1))
        elif i == len(points) - 2 and cap == 'square':
             polygons.append((_create_square_cap(p2, nx, ny, half_width, 1), 1))
            
        # Join (if not last segment)
        if i < len(points) - 2:
            p3 = points[i+2]
            # Simple approach: Round join for everything for now to handle corners
            # Real miter implementation is complex
            polygons.append((_create_round_join(p2, half_width), 1))
            
    return polygons

def _create_round_cap(center: Point, nx: float, ny: float, r: float) -> Polygon:
    """Create a round cap polygon."""
    points = []
    steps = 8
    # Angle of normal
    angle = math.atan2(ny, nx)
    
    for i in range(steps + 1):
        theta = angle + math.pi/2 + (math.pi * i / steps)
        px = center[0] + math.cos(theta) * r
        py = center[1] + math.sin(theta) * r
        points.append((px, py))
    return points

def _create_square_cap(center: Point, nx: float, ny: float, r: float, direction: int) -> Polygon:
    """Create a square cap polygon."""
    # direction: -1 for start, 1 for end
    dx, dy = -ny * direction, nx * direction # Tangent
    
    p1 = (center[0] + nx*r, center[1] + ny*r)
    p2 = (center[0] - nx*r, center[1] - ny*r)
    p3 = (p2[0] + dx*r, p2[1] + dy*r)
    p4 = (p1[0] + dx*r, p1[1] + dy*r)
    
    return [p1, p2, p3, p4]

def _create_round_join(center: Point, r: float) -> Polygon:
    """Create a simple circle for joins (lazy round join)."""
    points = []
    steps = 12
    for i in range(steps):
        theta = (2 * math.pi * i) / steps
        px = center[0] + math.cos(theta) * r
        py = center[1] + math.sin(theta) * r
        points.append((px, py))
    return points
