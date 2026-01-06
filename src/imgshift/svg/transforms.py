"""
Affine transformation matrix operations for SVG rendering.
"""

import math
import re
from typing import Tuple, List
from dataclasses import dataclass


@dataclass
class Matrix:
    """
    2D affine transformation matrix.
    
    Represents a 3x3 matrix:
    | a  c  e |
    | b  d  f |
    | 0  0  1 |
    """
    a: float = 1.0  # scale x
    b: float = 0.0  # skew y
    c: float = 0.0  # skew x
    d: float = 1.0  # scale y
    e: float = 0.0  # translate x
    f: float = 0.0  # translate y
    
    @classmethod
    def identity(cls) -> 'Matrix':
        """Create an identity matrix."""
        return cls()
    
    @classmethod
    def translate(cls, tx: float, ty: float = 0) -> 'Matrix':
        """Create a translation matrix."""
        return cls(e=tx, f=ty)
    
    @classmethod
    def scale(cls, sx: float, sy: float = None) -> 'Matrix':
        """Create a scale matrix."""
        if sy is None:
            sy = sx
        return cls(a=sx, d=sy)
    
    @classmethod
    def rotate(cls, angle: float, cx: float = 0, cy: float = 0) -> 'Matrix':
        """
        Create a rotation matrix.
        
        Args:
            angle: Rotation angle in degrees
            cx, cy: Center of rotation
        """
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        
        if cx == 0 and cy == 0:
            return cls(a=cos_a, b=sin_a, c=-sin_a, d=cos_a)
        
        # Rotate around point (cx, cy)
        return (
            cls.translate(cx, cy)
            .multiply(cls(a=cos_a, b=sin_a, c=-sin_a, d=cos_a))
            .multiply(cls.translate(-cx, -cy))
        )
    
    @classmethod
    def skew_x(cls, angle: float) -> 'Matrix':
        """Create a skew-X matrix."""
        return cls(c=math.tan(math.radians(angle)))
    
    @classmethod
    def skew_y(cls, angle: float) -> 'Matrix':
        """Create a skew-Y matrix."""
        return cls(b=math.tan(math.radians(angle)))
    
    def multiply(self, other: 'Matrix') -> 'Matrix':
        """Multiply this matrix with another (self * other)."""
        return Matrix(
            a=self.a * other.a + self.c * other.b,
            b=self.b * other.a + self.d * other.b,
            c=self.a * other.c + self.c * other.d,
            d=self.b * other.c + self.d * other.d,
            e=self.a * other.e + self.c * other.f + self.e,
            f=self.b * other.e + self.d * other.f + self.f,
        )
    
    def transform_point(self, x: float, y: float) -> Tuple[float, float]:
        """Apply the transformation to a point."""
        return (
            self.a * x + self.c * y + self.e,
            self.b * x + self.d * y + self.f,
        )
    
    def __repr__(self) -> str:
        return f"Matrix({self.a:.3f}, {self.b:.3f}, {self.c:.3f}, {self.d:.3f}, {self.e:.3f}, {self.f:.3f})"


def parse_transform(transform_str: str) -> Matrix:
    """
    Parse an SVG transform attribute into a Matrix.
    
    Supports:
        - translate(tx [, ty])
        - scale(sx [, sy])
        - rotate(angle [, cx, cy])
        - skewX(angle)
        - skewY(angle)
        - matrix(a, b, c, d, e, f)
    
    Args:
        transform_str: SVG transform attribute value
        
    Returns:
        Combined transformation matrix
    """
    if not transform_str:
        return Matrix.identity()
    
    result = Matrix.identity()
    
    # Pattern to match transform functions
    pattern = r'(translate|scale|rotate|skewX|skewY|matrix)\s*\(([^)]+)\)'
    
    for match in re.finditer(pattern, transform_str):
        func_name = match.group(1)
        args_str = match.group(2)
        
        # Parse arguments (comma or space separated)
        args = [float(x) for x in re.split(r'[\s,]+', args_str.strip()) if x]
        
        if func_name == 'translate':
            tx = args[0] if len(args) > 0 else 0
            ty = args[1] if len(args) > 1 else 0
            result = result.multiply(Matrix.translate(tx, ty))
            
        elif func_name == 'scale':
            sx = args[0] if len(args) > 0 else 1
            sy = args[1] if len(args) > 1 else sx
            result = result.multiply(Matrix.scale(sx, sy))
            
        elif func_name == 'rotate':
            angle = args[0] if len(args) > 0 else 0
            cx = args[1] if len(args) > 2 else 0
            cy = args[2] if len(args) > 2 else 0
            result = result.multiply(Matrix.rotate(angle, cx, cy))
            
        elif func_name == 'skewX':
            angle = args[0] if len(args) > 0 else 0
            result = result.multiply(Matrix.skew_x(angle))
            
        elif func_name == 'skewY':
            angle = args[0] if len(args) > 0 else 0
            result = result.multiply(Matrix.skew_y(angle))
            
        elif func_name == 'matrix':
            if len(args) >= 6:
                result = result.multiply(Matrix(
                    a=args[0], b=args[1], c=args[2],
                    d=args[3], e=args[4], f=args[5]
                ))
    
    return result
