"""
SVG rasterizer - converts SVG elements to pixel data.

Uses scanline rendering algorithm for fill and anti-aliased line drawing for strokes.
"""

from typing import List, Tuple, Optional
from imgshift.svg.parser import SVGDocument
from imgshift.svg.elements import Element
from imgshift.svg.transforms import Matrix
import math


class PixelBuffer:
    """RGBA pixel buffer for rendering."""
    
    def __init__(self, width: int, height: int, background: Tuple[int, int, int, int] = (255, 255, 255, 255)):
        """
        Initialize a pixel buffer.
        
        Args:
            width: Width in pixels
            height: Height in pixels
            background: Background color (R, G, B, A)
        """
        self.width = width
        self.height = height
        # Store as flat list of RGBA tuples for efficiency
        self.pixels: List[List[int]] = [[background[0], background[1], background[2], background[3]] 
                                         for _ in range(width * height)]
    
    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int, int]):
        """Set a pixel with alpha blending."""
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = y * self.width + x
            self._blend_pixel(idx, color)
    
    def _blend_pixel(self, idx: int, color: Tuple[int, int, int, int]):
        """Blend a color onto an existing pixel using alpha compositing."""
        sr, sg, sb, sa = color
        if sa == 0:
            return
        
        if sa == 255:
            self.pixels[idx] = [sr, sg, sb, 255]
            return
        
        dr, dg, db, da = self.pixels[idx]
        
        # Alpha compositing
        sa_norm = sa / 255.0
        da_norm = da / 255.0
        
        out_a = sa_norm + da_norm * (1 - sa_norm)
        if out_a > 0:
            out_r = (sr * sa_norm + dr * da_norm * (1 - sa_norm)) / out_a
            out_g = (sg * sa_norm + dg * da_norm * (1 - sa_norm)) / out_a
            out_b = (sb * sa_norm + db * da_norm * (1 - sa_norm)) / out_a
            self.pixels[idx] = [int(out_r), int(out_g), int(out_b), int(out_a * 255)]
    
    def get_rows(self) -> List[List[Tuple[int, int, int, int]]]:
        """Get pixel data as rows of RGBA tuples."""
        rows = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                idx = y * self.width + x
                p = self.pixels[idx]
                row.append((p[0], p[1], p[2], p[3]))
            rows.append(row)
        return rows
    
    def get_flat_rgba(self) -> bytes:
        """Get pixel data as flat RGBA bytes."""
        data = bytearray()
        for pixel in self.pixels:
            data.extend(pixel)
        return bytes(data)


class Rasterizer:
    """Converts SVG documents to pixel buffers."""
    
    def __init__(self, antialias: bool = True):
        """
        Initialize the rasterizer.
        
        Args:
            antialias: Whether to use anti-aliasing for strokes
        """
        self.antialias = antialias
    
    def render(self, doc: SVGDocument, width: Optional[int] = None, 
               height: Optional[int] = None, 
               background: Tuple[int, int, int, int] = (255, 255, 255, 255)) -> PixelBuffer:
        """
        Render an SVG document to a pixel buffer.
        
        Args:
            doc: Parsed SVG document
            width: Output width (optional, uses document size if not specified)
            height: Output height (optional, uses document size if not specified)
            background: Background color (R, G, B, A)
            
        Returns:
            PixelBuffer with rendered image
        """
        # Calculate output size
        out_width, out_height = doc.get_size(width, height)
        
        # Get viewBox transform
        vb_transform = doc.get_transform(out_width, out_height)
        
        # Create pixel buffer
        buffer = PixelBuffer(out_width, out_height, background)
        
        # Render each element
        for element in doc.elements:
            self._render_element(buffer, element, vb_transform)
        
        return buffer
    
    def _render_element(self, buffer: PixelBuffer, element: Element, 
                        global_transform: Matrix):
        """Render a single element to the buffer."""
        # Get polygons with combined transform
        polygons = element.get_polygons()
        
        # Apply global (viewBox) transform to all points
        transformed = []
        for polygon in polygons:
            pts = [global_transform.transform_point(x, y) for x, y in polygon]
            transformed.append(pts)
        
        # Render fill
        fill_color = element.style.get_fill_color()
        if fill_color[3] > 0:
            for polygon in transformed:
                self._fill_polygon(buffer, polygon, fill_color)
        
        # Render stroke
        stroke_color = element.style.get_stroke_color()
        if stroke_color[3] > 0 and element.style.stroke_width > 0:
            # Scale stroke width by transform
            stroke_width = element.style.stroke_width
            for polygon in transformed:
                self._stroke_polygon(buffer, polygon, stroke_color, stroke_width)
    
    def _fill_polygon(self, buffer: PixelBuffer, polygon: List[Tuple[float, float]], 
                      color: Tuple[int, int, int, int]):
        """Fill a polygon using scanline algorithm."""
        if len(polygon) < 3:
            return
        
        # Find bounding box
        min_y = max(0, int(min(p[1] for p in polygon)))
        max_y = min(buffer.height - 1, int(max(p[1] for p in polygon)))
        
        # Scanline fill
        for y in range(min_y, max_y + 1):
            # Find intersections with polygon edges
            intersections = []
            
            for i in range(len(polygon) - 1):
                x1, y1 = polygon[i]
                x2, y2 = polygon[i + 1]
                
                # Check if edge crosses scanline
                if (y1 <= y < y2) or (y2 <= y < y1):
                    if y2 != y1:
                        x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                        intersections.append(x)
            
            # Sort intersections
            intersections.sort()
            
            # Fill between pairs
            for i in range(0, len(intersections) - 1, 2):
                x_start = max(0, int(intersections[i]))
                x_end = min(buffer.width - 1, int(intersections[i + 1]))
                
                for x in range(x_start, x_end + 1):
                    buffer.set_pixel(x, y, color)
    
    def _stroke_polygon(self, buffer: PixelBuffer, polygon: List[Tuple[float, float]],
                        color: Tuple[int, int, int, int], width: float):
        """Draw the outline of a polygon."""
        if len(polygon) < 2:
            return
        
        for i in range(len(polygon) - 1):
            x1, y1 = polygon[i]
            x2, y2 = polygon[i + 1]
            
            if self.antialias:
                self._draw_line_aa(buffer, x1, y1, x2, y2, color, width)
            else:
                self._draw_line(buffer, x1, y1, x2, y2, color, width)
    
    def _draw_line(self, buffer: PixelBuffer, x1: float, y1: float,
                   x2: float, y2: float, color: Tuple[int, int, int, int], 
                   width: float):
        """Draw a line using Bresenham's algorithm."""
        # Simple line for thin strokes
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        x, y = int(x1), int(y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        
        if dx > dy:
            err = dx / 2
            while x != int(x2):
                buffer.set_pixel(x, y, color)
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2
            while y != int(y2):
                buffer.set_pixel(x, y, color)
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        
        buffer.set_pixel(int(x2), int(y2), color)
    
    def _draw_line_aa(self, buffer: PixelBuffer, x1: float, y1: float,
                      x2: float, y2: float, color: Tuple[int, int, int, int],
                      width: float):
        """Draw an anti-aliased line using Xiaolin Wu's algorithm."""
        r, g, b, a = color
        
        def plot(x: int, y: int, brightness: float):
            if brightness <= 0:
                return
            alpha = int(a * brightness)
            buffer.set_pixel(x, y, (r, g, b, alpha))
        
        def fpart(x: float) -> float:
            return x - int(x)
        
        def rfpart(x: float) -> float:
            return 1 - fpart(x)
        
        steep = abs(y2 - y1) > abs(x2 - x1)
        
        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
        
        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
        
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0:
            gradient = 1.0
        else:
            gradient = dy / dx
        
        # Handle first endpoint
        xend = round(x1)
        yend = y1 + gradient * (xend - x1)
        xgap = rfpart(x1 + 0.5)
        xpxl1 = int(xend)
        ypxl1 = int(yend)
        
        if steep:
            plot(ypxl1, xpxl1, rfpart(yend) * xgap)
            plot(ypxl1 + 1, xpxl1, fpart(yend) * xgap)
        else:
            plot(xpxl1, ypxl1, rfpart(yend) * xgap)
            plot(xpxl1, ypxl1 + 1, fpart(yend) * xgap)
        
        intery = yend + gradient
        
        # Handle second endpoint
        xend = round(x2)
        yend = y2 + gradient * (xend - x2)
        xgap = fpart(x2 + 0.5)
        xpxl2 = int(xend)
        ypxl2 = int(yend)
        
        if steep:
            plot(ypxl2, xpxl2, rfpart(yend) * xgap)
            plot(ypxl2 + 1, xpxl2, fpart(yend) * xgap)
        else:
            plot(xpxl2, ypxl2, rfpart(yend) * xgap)
            plot(xpxl2, ypxl2 + 1, fpart(yend) * xgap)
        
        # Main loop
        if steep:
            for x in range(xpxl1 + 1, xpxl2):
                plot(int(intery), x, rfpart(intery))
                plot(int(intery) + 1, x, fpart(intery))
                intery += gradient
        else:
            for x in range(xpxl1 + 1, xpxl2):
                plot(x, int(intery), rfpart(intery))
                plot(x, int(intery) + 1, fpart(intery))
                intery += gradient
