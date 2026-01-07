"""
SVG path command parser.

Parses the 'd' attribute of SVG <path> elements into a list of commands.
"""

import re
import math
from typing import List, Tuple, NamedTuple
from dataclasses import dataclass


class PathCommand(NamedTuple):
    """Represents a single path command."""
    command: str  # M, L, H, V, C, S, Q, T, A, Z (uppercase = absolute)
    args: Tuple[float, ...]


def parse_path(d: str) -> List[PathCommand]:
    """
    Parse an SVG path 'd' attribute into a list of commands.
    
    Supports all SVG path commands:
        M/m - moveto
        L/l - lineto
        H/h - horizontal lineto
        V/v - vertical lineto
        C/c - cubic bezier
        S/s - smooth cubic bezier
        Q/q - quadratic bezier
        T/t - smooth quadratic bezier
        A/a - arc
        Z/z - closepath
    
    Args:
        d: SVG path 'd' attribute value
        
    Returns:
        List of PathCommand tuples
    """
    if not d:
        return []
    
    commands = []
    
    # Tokenize: split into commands and numbers
    # Commands are single letters, numbers can be integers, floats, or scientific notation
    token_pattern = r'([MmLlHhVvCcSsQqTtAaZz])|([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)'
    tokens = []
    
    for match in re.finditer(token_pattern, d):
        if match.group(1):
            tokens.append(match.group(1))
        else:
            tokens.append(float(match.group(2)))
    
    # Process tokens
    i = 0
    current_command = None
    
    while i < len(tokens):
        token = tokens[i]
        
        if isinstance(token, str):
            current_command = token
            i += 1
        
        if current_command is None:
            i += 1
            continue
        
        cmd = current_command.upper()
        
        # Z/z takes no arguments
        if cmd == 'Z':
            commands.append(PathCommand(current_command, ()))
            current_command = None
            continue
        
        # Get required number of arguments for command
        arg_counts = {
            'M': 2, 'L': 2, 'H': 1, 'V': 1,
            'C': 6, 'S': 4, 'Q': 4, 'T': 2,
            'A': 7
        }
        
        num_args = arg_counts.get(cmd, 0)
        
        if num_args == 0:
            continue
        
        # Collect arguments
        args = []
        while len(args) < num_args and i < len(tokens):
            if isinstance(tokens[i], (int, float)):
                args.append(float(tokens[i]))
                i += 1
            else:
                break
        
        if len(args) == num_args:
            commands.append(PathCommand(current_command, tuple(args)))
            
            # After M, subsequent coordinate pairs are treated as L
            if current_command == 'M':
                current_command = 'L'
            elif current_command == 'm':
                current_command = 'l'
    
    return commands


def calculate_winding_direction(polygon: List[Tuple[float, float]]) -> int:
    """
    Calculate winding direction of a polygon using the shoelace formula.
    
    Returns:
        +1 for clockwise winding
        -1 for counterclockwise winding
        +1 if polygon is degenerate (area = 0)
    """
    if len(polygon) < 3:
        return 1  # Degenerate case
    
    # Shoelace formula for signed area
    signed_area = 0.0
    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]
        signed_area += (x2 - x1) * (y2 + y1)
    
    # In SVG coordinate system (Y increases downward):
    # Negative area = clockwise (normal outer paths)
    # Positive area = counterclockwise (holes)
    if signed_area < 0:
        return 1  # Clockwise
    elif signed_area > 0:
        return -1  # Counterclockwise
    else:
        return 1  # Degenerate (zero area)


def path_to_points(commands: List[PathCommand], resolution: int = 20) -> List[Tuple[List[Tuple[float, float]], int]]:
    """
    Convert path commands to a list of subpaths (polygons) with winding direction.
    
    Bezier curves are approximated with line segments.
    
    Args:
        commands: List of PathCommand from parse_path()
        resolution: Number of segments per bezier curve (ignored for adaptive bezier)
        
    Returns:
        List of (polygon, direction) tuples where:
        - polygon: List of (x, y) points
        - direction: +1 for clockwise, -1 for counterclockwise
    """
    subpaths = []
    current_path: List[Tuple[float, float]] = []
    
    x, y = 0.0, 0.0  # Current position
    start_x, start_y = 0.0, 0.0  # Start of current subpath
    last_control = None  # Last control point for S/T commands
    
    for cmd in commands:
        command = cmd.command
        args = cmd.args
        is_relative = command.islower()
        command = command.upper()
        
        if command == 'M':
            # Start new subpath
            if current_path:
                direction = calculate_winding_direction(current_path)
                subpaths.append((current_path, direction))
            
            if is_relative:
                x += args[0]
                y += args[1]
            else:
                x, y = args[0], args[1]
            
            start_x, start_y = x, y
            current_path = [(x, y)]
            last_control = None
            
        elif command == 'L':
            if is_relative:
                x += args[0]
                y += args[1]
            else:
                x, y = args[0], args[1]
            current_path.append((x, y))
            last_control = None
            
        elif command == 'H':
            if is_relative:
                x += args[0]
            else:
                x = args[0]
            current_path.append((x, y))
            last_control = None
            
        elif command == 'V':
            if is_relative:
                y += args[0]
            else:
                y = args[0]
            current_path.append((x, y))
            last_control = None
            
        elif command == 'C':
            # Cubic bezier
            if is_relative:
                x1, y1 = x + args[0], y + args[1]
                x2, y2 = x + args[2], y + args[3]
                x3, y3 = x + args[4], y + args[5]
            else:
                x1, y1 = args[0], args[1]
                x2, y2 = args[2], args[3]
                x3, y3 = args[4], args[5]
            
            points = cubic_bezier(x, y, x1, y1, x2, y2, x3, y3, resolution)
            current_path.extend(points[1:])  # Skip first point (current pos)
            x, y = x3, y3
            last_control = (x2, y2)
            
        elif command == 'S':
            # Smooth cubic bezier
            if last_control:
                x1 = 2 * x - last_control[0]
                y1 = 2 * y - last_control[1]
            else:
                x1, y1 = x, y
            
            if is_relative:
                x2, y2 = x + args[0], y + args[1]
                x3, y3 = x + args[2], y + args[3]
            else:
                x2, y2 = args[0], args[1]
                x3, y3 = args[2], args[3]
            
            points = cubic_bezier(x, y, x1, y1, x2, y2, x3, y3, resolution)
            current_path.extend(points[1:])
            x, y = x3, y3
            last_control = (x2, y2)
            
        elif command == 'Q':
            # Quadratic bezier
            if is_relative:
                x1, y1 = x + args[0], y + args[1]
                x2, y2 = x + args[2], y + args[3]
            else:
                x1, y1 = args[0], args[1]
                x2, y2 = args[2], args[3]
            
            points = quadratic_bezier(x, y, x1, y1, x2, y2, resolution)
            current_path.extend(points[1:])
            x, y = x2, y2
            last_control = (x1, y1)
            
        elif command == 'T':
            # Smooth quadratic bezier
            if last_control:
                x1 = 2 * x - last_control[0]
                y1 = 2 * y - last_control[1]
            else:
                x1, y1 = x, y
            
            if is_relative:
                x2, y2 = x + args[0], y + args[1]
            else:
                x2, y2 = args[0], args[1]
            
            points = quadratic_bezier(x, y, x1, y1, x2, y2, resolution)
            current_path.extend(points[1:])
            x, y = x2, y2
            last_control = (x1, y1)
            
        elif command == 'A':
            # Arc
            rx, ry = args[0], args[1]
            rotation = args[2]
            large_arc = int(args[3])
            sweep = int(args[4])
            
            if is_relative:
                end_x, end_y = x + args[5], y + args[6]
            else:
                end_x, end_y = args[5], args[6]
            
            points = arc_to_bezier(x, y, rx, ry, rotation, large_arc, sweep, end_x, end_y, resolution)
            current_path.extend(points[1:])
            x, y = end_x, end_y
            last_control = None
            
        elif command == 'Z':
            # Close path
            if current_path:
                current_path.append((start_x, start_y))
            x, y = start_x, start_y
            last_control = None
    
    # Add final subpath with winding direction
    if current_path:
        direction = calculate_winding_direction(current_path)
        subpaths.append((current_path, direction))
    
    return subpaths

def distance_sq(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2

def cubic_bezier(x0: float, y0: float, x1: float, y1: float, 
                 x2: float, y2: float, x3: float, y3: float, 
                 resolution: int = 10) -> List[Tuple[float, float]]:
    """
    Generate points for a cubic bezier curve using adaptive subdivision.
    resolution param is kept for compatibility but ignores it in favor of adaptive tolerance.
    """
    points = [(x0, y0)]
    # Use a fixed tolerance suitable for pixel rendering
    _recursive_cubic_bezier(x0, y0, x1, y1, x2, y2, x3, y3, points, distance_tolerance_sq=0.5)
    points.append((x3, y3))
    return points

def _recursive_cubic_bezier(x0, y0, x1, y1, x2, y2, x3, y3, points, distance_tolerance_sq):
    """Recursively subdivide Bezier curve until flat."""
    
    # Midpoints
    x01 = (x0 + x1) / 2
    y01 = (y0 + y1) / 2
    x12 = (x1 + x2) / 2
    y12 = (y1 + y2) / 2
    x23 = (x2 + x3) / 2
    y23 = (y2 + y3) / 2
    
    x012 = (x01 + x12) / 2
    y012 = (y01 + y12) / 2
    x123 = (x12 + x23) / 2
    y123 = (y12 + y23) / 2
    
    x0123 = (x012 + x123) / 2
    y0123 = (y012 + y123) / 2
    
    dx = x3 - x0
    dy = y3 - y0
    d_sq = dx*dx + dy*dy
    
    flat = False
    
    if d_sq < 1e-6:
        # Endpoints are very close
        d1 = distance_sq((x0, y0), (x1, y1))
        d2 = distance_sq((x0, y0), (x2, y2))
        if d1 < distance_tolerance_sq and d2 < distance_tolerance_sq:
            flat = True
    else:
        # Distance from point to line (approximation)
        # Using control points distance to baseline
        # Robust flatness test is expensive, use simple subdivision limit
        
        # Simple test: if midpoint of curve is close to midpoint of baseline
        mx = (x0 + x3) / 2
        my = (y0 + y3) / 2
        dist_sq = (x0123 - mx)**2 + (y0123 - my)**2
        
        if dist_sq < 0.1: # Tolerance
             flat = True

    if flat:
        return

    _recursive_cubic_bezier(x0, y0, x01, y01, x012, y012, x0123, y0123, points, distance_tolerance_sq)
    points.append((x0123, y0123))
    _recursive_cubic_bezier(x0123, y0123, x123, y123, x23, y23, x3, y3, points, distance_tolerance_sq)


def quadratic_bezier(x0: float, y0: float, x1: float, y1: float, x2: float, y2: float, resolution: int = 10) -> List[Tuple[float, float]]:
    """Convert quadratic to cubic and use cubic solver."""
    cx1 = x0 + (2/3) * (x1 - x0)
    cy1 = y0 + (2/3) * (y1 - y0)
    cx2 = x2 + (2/3) * (x1 - x2)
    cy2 = y2 + (2/3) * (y1 - y2)
    return cubic_bezier(x0, y0, cx1, cy1, cx2, cy2, x2, y2, resolution)


def arc_to_bezier(x0: float, y0: float, rx: float, ry: float,
                  rotation: float, large_arc: int, sweep: int,
                  x1: float, y1: float, segments: int) -> List[Tuple[float, float]]:
    """
    Convert an elliptical arc to bezier curve points.
    
    Based on the SVG arc parameterization algorithm.
    """
    if rx == 0 or ry == 0:
        return [(x1, y1)]
    
    rx = abs(rx)
    ry = abs(ry)
    
    # Convert rotation to radians
    phi = math.radians(rotation)
    cos_phi = math.cos(phi)
    sin_phi = math.sin(phi)
    
    # Compute midpoint in rotated coordinates
    dx = (x0 - x1) / 2
    dy = (y0 - y1) / 2
    x1p = cos_phi * dx + sin_phi * dy
    y1p = -sin_phi * dx + cos_phi * dy
    
    # Scale radii if necessary
    lambda_sq = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lambda_sq > 1:
        lambda_val = math.sqrt(lambda_sq)
        rx *= lambda_val
        ry *= lambda_val
    
    # Compute center in rotated coordinates
    sq = max(0, (rx*rx * ry*ry - rx*rx * y1p*y1p - ry*ry * x1p*x1p) / 
             (rx*rx * y1p*y1p + ry*ry * x1p*x1p))
    
    coef = math.sqrt(sq)
    if large_arc == sweep:
        coef = -coef
    
    cxp = coef * rx * y1p / ry
    cyp = -coef * ry * x1p / rx
    
    # Convert center back to original coordinates
    cx = cos_phi * cxp - sin_phi * cyp + (x0 + x1) / 2
    cy = sin_phi * cxp + cos_phi * cyp + (y0 + y1) / 2
    
    # Compute start and end angles
    def angle(ux, uy, vx, vy):
        n = math.sqrt(ux*ux + uy*uy) * math.sqrt(vx*vx + vy*vy)
        if n == 0:
            return 0
        c = (ux*vx + uy*vy) / n
        c = max(-1, min(1, c))
        sign = 1 if ux*vy - uy*vx >= 0 else -1
        return sign * math.acos(c)
    
    theta1 = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = angle((x1p - cxp) / rx, (y1p - cyp) / ry,
                   (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    
    if sweep == 0 and dtheta > 0:
        dtheta -= 2 * math.pi
    elif sweep == 1 and dtheta < 0:
        dtheta += 2 * math.pi
    
    # Generate points
    # For arc, we still use fixed segments for now as adaptive arc subdivision is more complex
    # and arcs are usually smaller parts
    points = []
    for i in range(segments + 1):
        t = theta1 + (i / segments) * dtheta
        
        # Point on ellipse in rotated coordinates
        px = rx * math.cos(t)
        py = ry * math.sin(t)
        
        # Rotate and translate
        x = cos_phi * px - sin_phi * py + cx
        y = sin_phi * px + cos_phi * py + cy
        points.append((x, y))
    
    return points
