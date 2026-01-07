"""
Paint Server architecture for SVG rendering.

This module defines how colors and gradients are calculated per pixel.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import math
from imgshift.svg.transforms import Matrix

Color = Tuple[int, int, int, int]

@dataclass
class GradientStop:
    """A stop in a gradient."""
    offset: float
    color: Color

class Paint(ABC):
    """Abstract base class for paint servers."""
    
    @abstractmethod
    def get_color(self, x: float, y: float) -> Color:
        """Get color at specific user-space coordinates."""
        pass

@dataclass
class SolidColor(Paint):
    """A solid simple color."""
    color: Color
    
    def get_color(self, x: float, y: float) -> Color:
        return self.color

class Gradient(Paint):
    """Base class for gradients."""
    def __init__(self, stops: List[GradientStop], transform: Matrix = Matrix.identity(), spread_method: str = 'pad', units: str = 'objectBoundingBox'):
        self.stops = sorted(stops, key=lambda s: s.offset)
        self.transform = transform
        self.spread_method = spread_method
        self.units = units
        # Pre-calculate inverse transform for mapping screen coords back to gradient space
        self.inv_transform = transform.inverse()

    def _get_stop_color(self, t: float) -> Color:
        """Get interpolated color at position t (0.0 to 1.0)."""
        # Handle spread methods
        if self.spread_method == 'pad':
            t = max(0.0, min(1.0, t))
        elif self.spread_method == 'reflect':
            t = abs(t) % 2.0
            if t > 1.0:
                t = 2.0 - t
        elif self.spread_method == 'repeat':
            t = t % 1.0
            if t < 0: t += 1.0
            
        # Find spans
        if not self.stops:
            return (0, 0, 0, 0)
        
        if t <= self.stops[0].offset:
            return self.stops[0].color
        if t >= self.stops[-1].offset:
            return self.stops[-1].color
            
        for i in range(len(self.stops) - 1):
            s1 = self.stops[i]
            s2 = self.stops[i+1]
            if s1.offset <= t <= s2.offset:
                # Interpolate
                denom = s2.offset - s1.offset
                if denom == 0:
                    return s1.color
                
                ratio = (t - s1.offset) / denom
                
                r1, g1, b1, a1 = s1.color
                r2, g2, b2, a2 = s2.color
                
                return (
                    int(r1 + (r2 - r1) * ratio),
                    int(g1 + (g2 - g1) * ratio),
                    int(b1 + (b2 - b1) * ratio),
                    int(a1 + (a2 - a1) * ratio)
                )
        return self.stops[-1].color

class LinearGradient(Gradient):
    """Linear gradient implementation."""
    def __init__(self, x1: float, y1: float, x2: float, y2: float, stops: List[GradientStop], **kwargs):
        super().__init__(stops, **kwargs)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        
        # Pre-calculate calculation constants
        self.dx = x2 - x1
        self.dy = y2 - y1
        self.len_sq = self.dx*self.dx + self.dy*self.dy
        
    def get_color(self, x: float, y: float) -> Color:
        # Transform point to gradient space
        # Note: If objectBoundingBox, x/y must be transformed BEFORE calling get_color
        # or we need to pass bbox here. 
        # Current design: caller (Rasterizer) is responsible for mapping BBox -> Unit Square
        # if units='objectBoundingBox'
        
        tx, ty = self.inv_transform.transform_point(x, y)
        
        if self.len_sq == 0:
            return self._get_stop_color(0)
            
        # Project point onto gradient vector line
        # t = ((px - x1)*dx + (py - y1)*dy) / len_sq
        t = ((tx - self.x1) * self.dx + (ty - self.y1) * self.dy) / self.len_sq
        
        return self._get_stop_color(t)

class RadialGradient(Gradient):
    """Radial gradient implementation."""
    def __init__(self, cx: float, cy: float, r: float, fx: float, fy: float, stops: List[GradientStop], **kwargs):
        super().__init__(stops, **kwargs)
        self.cx = cx
        self.cy = cy
        self.r = r
        self.fx = fx  # Focal point
        self.fy = fy
        
    def get_color(self, x: float, y: float) -> Color:
        # Transform point
        tx, ty = self.inv_transform.transform_point(x, y)
        
        # Simple radial gradient (ignoring focal point complexity for now to keep it simpler)
        # Standard SVG radial gradient where focus is center: distance from center / radius
        
        dx = tx - self.cx
        dy = ty - self.cy
        dist = math.sqrt(dx*dx + dy*dy)
        
        if self.r == 0:
            return self._get_stop_color(0)
            
        t = dist / self.r
        
        return self._get_stop_color(t)
