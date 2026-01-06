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


def path_to_points(commands: List[PathCommand], resolution: int = 20) -> List[List[Tuple[float, float]]]:
    """
    Convert path commands to a list of subpaths (polygons).
    
    Bezier curves are approximated with line segments.
    
    Args:
        commands: List of PathCommand from parse_path()
        resolution: Number of segments per bezier curve
        
    Returns:
        List of subpaths, where each subpath is a list of (x, y) points
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
                subpaths.append(current_path)
            
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
    
    if current_path:
        subpaths.append(current_path)
    
    return subpaths


def cubic_bezier(x0: float, y0: float, x1: float, y1: float, 
                 x2: float, y2: float, x3: float, y3: float, 
                 segments: int) -> List[Tuple[float, float]]:
    """Generate points along a cubic bezier curve."""
    points = []
    for i in range(segments + 1):
        t = i / segments
        t2 = t * t
        t3 = t2 * t
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt
        
        px = mt3 * x0 + 3 * mt2 * t * x1 + 3 * mt * t2 * x2 + t3 * x3
        py = mt3 * y0 + 3 * mt2 * t * y1 + 3 * mt * t2 * y2 + t3 * y3
        points.append((px, py))
    
    return points


def quadratic_bezier(x0: float, y0: float, x1: float, y1: float,
                     x2: float, y2: float, segments: int) -> List[Tuple[float, float]]:
    """Generate points along a quadratic bezier curve."""
    points = []
    for i in range(segments + 1):
        t = i / segments
        mt = 1 - t
        
        px = mt * mt * x0 + 2 * mt * t * x1 + t * t * x2
        py = mt * mt * y0 + 2 * mt * t * y1 + t * t * y2
        points.append((px, py))
    
    return points


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
