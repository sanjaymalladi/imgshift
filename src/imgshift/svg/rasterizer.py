"""
SVG rasterizer - converts SVG elements to pixel data.

Uses scanline rendering algorithm for fill and anti-aliased line drawing for strokes.
"""

from typing import List, Tuple, Optional, Any
from imgshift.svg.parser import SVGDocument
from imgshift.svg.elements import Element, Text, Group
from imgshift.svg.transforms import Matrix
from imgshift.svg.paint import Paint, SolidColor, Gradient
from imgshift.svg.geometry import stroke_polyline
import math

# Import Pillow for Text rendering
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

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
        self.antialias = antialias
    
    def render(self, doc: SVGDocument, width: Optional[int] = None, 
               height: Optional[int] = None, 
               background: Tuple[int, int, int, int] = (255, 255, 255, 255)) -> PixelBuffer:
        """Render an SVG document to a pixel buffer."""
        # Calculate output size
        out_width, out_height = doc.get_size(width, height)
        
        # Get viewBox transform
        vb_transform = doc.get_transform(out_width, out_height)
        
        # Create pixel buffer
        buffer = PixelBuffer(out_width, out_height, background)
        
        # Render each element
        for element in doc.elements:
            self._render_element(buffer, element, vb_transform, doc)
        
        return buffer
    
    def _resolve_paint(self, paint_ref: Any, doc: SVGDocument) -> Optional[Paint]:
        """Resolve a paint reference to a Paint object."""
        if isinstance(paint_ref, Paint):
            return paint_ref
        
        if isinstance(paint_ref, str) and paint_ref.startswith('url('):
            # Extract ID: url(#id) -> id
            pid = paint_ref[4:-1].replace('#', '').strip()
            if pid in doc.defs:
                return doc.defs[pid]
            # Fallback to gray if not found (debug)
            return SolidColor((128, 128, 128, 255))
            
        return None

    def _render_element(self, buffer: PixelBuffer, element: Element, 
                        global_transform: Matrix, doc: SVGDocument):
        """Render a single element to the buffer."""
        # Special handling for Group
        if isinstance(element, Group):
            # Push layer if group has opacity or transform needs isolation
            opacity = element.style.opacity
            
            # Check for group transform
            group_transform = global_transform.multiply(element.transform)
            
            if opacity < 1.0:
                # Need a temporary buffer for the group
                # Create a temporary buffer with the same size
                group_buffer = PixelBuffer(buffer.width, buffer.height, (0, 0, 0, 0))
                
                for child in element.children:
                    self._render_element(group_buffer, child, group_transform, doc)
                
                # Blend group buffer onto main buffer with opacity
                rows = group_buffer.get_rows()
                for y in range(buffer.height):
                    for x in range(buffer.width):
                        r, g, b, a = rows[y][x]
                        if a > 0:
                            # Apply group opacity
                            final_a = int(a * opacity)
                            buffer.set_pixel(x, y, (r, g, b, final_a))
                return
            else:
                 # Just render children directly
                for child in element.children:
                    self._render_element(buffer, child, group_transform, doc)
                return

        # Special handling for Text
        if isinstance(element, Text):
            self._render_text(buffer, element, global_transform, doc)
            return

        # Get bounding box for paint server
        bbox = element.get_bbox()

        # Get polygons with winding direction
        polygons_with_dir = getattr(element, 'to_polygons', lambda: [])()
        
        # Apply global (viewBox/parent) transform to all points
        transformed = []
        for polygon, direction in polygons_with_dir:
            pts = [global_transform.transform_point(x, y) for x, y in polygon]
            transformed.append((pts, direction))
        
        # Calculate inverse transform for gradient mapping (Device -> User)
        total_transform = global_transform.multiply(element.transform)
        pixel_to_user = total_transform.inverse()
        
        # Render stroke
        stroke_paint = self._resolve_paint(element.style.stroke, doc)
        stroke_width = element.style.stroke_width
        
        if stroke_paint and isinstance(stroke_paint, SolidColor) and stroke_width > 0:
            stroke_color = stroke_paint.color
            if stroke_color[3] > 0:
                # Scale stroke width
                scale_factor = math.sqrt(global_transform.a * global_transform.a + global_transform.c * global_transform.c)
                actual_width = stroke_width * scale_factor
                
                # Generate stroke geometry
                stroke_polygons = []
                for polygon, _ in transformed:  # Ignore direction for extracting polygon
                     stroke_polygons.extend(stroke_polyline(polygon, actual_width))
                
                # Strokes always nonzero
                self._fill_polygons(buffer, stroke_polygons, stroke_paint, pixel_to_user, fill_rule='nonzero', bbox=bbox)
                
        # Fill
        fill_paint = self._resolve_paint(element.style.fill, doc)
        if fill_paint:
            if isinstance(fill_paint, SolidColor) and fill_paint.color[3] == 0:
                pass
            else:
                self._fill_polygons(buffer, transformed, fill_paint, pixel_to_user, fill_rule=element.style.fill_rule, bbox=bbox)
    
    def _fill_polygons(self, buffer: PixelBuffer, polygons: List[Tuple[List[Tuple[float, float]], int]], 
                       paint: Paint, pixel_to_user: Matrix, fill_rule: str = 'nonzero', 
                       bbox: Optional[Tuple[float, float, float, float]] = None):
        """
        Fill multiple polygons using Scanline algorithm with winding rules.
        
        Args:
            polygons: List of (polygon, direction) tuples where direction is +1 (CW) or -1 (CCW)
            paint: Paint object
            pixel_to_user: Transform from pixel to user coordinates
            fill_rule: 'nonzero' or 'evenodd'
            bbox: Optional bounding box for objectBoundingBox gradients
        """
        if not polygons:
            return

        # Handle objectBoundingBox units for gradients
        effective_pixel_to_user = pixel_to_user
        if hasattr(paint, 'units') and paint.units == 'objectBoundingBox' and bbox:
            min_x, min_y, width, height = bbox
            if width > 0 and height > 0:
                # Map User Space -> Unit Square (0..1)
                # T_bbox = Scale(1/w, 1/h) * Translate(-x, -y)
                t_bbox = Matrix(1/width, 0, 0, 1/height, -min_x/width, -min_y/height)
                
                # Effective = T_bbox * pixel_to_user
                # Maps Pixel -> User -> Unit
                effective_pixel_to_user = t_bbox.multiply(pixel_to_user)
            
        # Get bounding box for optimization
        min_y = buffer.height
        max_y = -1
        
        # Build Edge Table (ET) with polygon ID tracking
        all_edges = []
        
        for poly_idx, (poly, poly_direction) in enumerate(polygons):
            for x, y in poly:
                min_y = min(min_y, int(y))
                max_y = max(max_y, int(y))
            
            # Create edges
            for i in range(len(poly)):
                p1 = poly[i]
                p2 = poly[(i + 1) % len(poly)]
                if int(p1[1]) == int(p2[1]): continue 
                
                y1, y2 = p1[1], p2[1]
                x1, x2 = p1[0], p2[0]
                
                # Edge direction: +1 if going down (y1 < y2), -1 if going up
                edge_direction = 1
                if y1 > y2:
                    y1, y2 = y2, y1
                    x1, x2 = x2, x1
                    edge_direction = -1
                
                dy = y2 - y1
                dx = x2 - x1
                inv_slope = dx / dy
                
                # Effective direction = edge_direction * poly_direction
                # For outer path (CW, +1): down edge contributes +1, up edge -1
                # For hole path (CCW, -1): down edge contributes -1, up edge +1
                effective_direction = edge_direction * poly_direction
                
                all_edges.append([y1, y2, x1, inv_slope, effective_direction])

        min_y = max(0, min_y)
        max_y = min(buffer.height - 1, max_y)
        
        # Deterministic edge sorting: (y_start, x_start, slope) for consistency
        all_edges.sort(key=lambda e: (e[0], e[2], e[3]))
        
        active_edges = []
        edge_idx = 0
        
        for y in range(min_y, max_y + 1):
            # Top-inclusive: add edges starting at this scanline
            while edge_idx < len(all_edges) and all_edges[edge_idx][0] <= y:
                 if all_edges[edge_idx][0] <= y:
                    e = all_edges[edge_idx]
                    active_edges.append([e[1], e[2], e[3], e[4]])
                 edge_idx += 1
            
            # Bottom-exclusive: remove edges ending before this scanline
            active_edges = [e for e in active_edges if e[0] > y + 1]
            
            # Sort by x position, then slope for determinism
            active_edges.sort(key=lambda e: (e[1], e[2]))
            
            if not active_edges:
                continue
            
            # Fill-rule implementation
            if fill_rule == 'evenodd':
                # Evenodd: Simple parity toggle, ignore winding direction
                fill_on = False
                for i in range(len(active_edges) - 1):
                    edge = active_edges[i]
                    next_edge = active_edges[i+1]
                    
                    # Toggle fill state at each edge crossing
                    fill_on = not fill_on
                    
                    if fill_on:
                        # Fill run
                        x_start = max(0, int(edge[1] + 0.5))
                        x_end = min(buffer.width - 1, int(next_edge[1] + 0.5))
                        
                        if x_start <= x_end:
                             for x in range(x_start, x_end + 1):
                                # Sample paint with EFFECTIVE transform
                                ux, uy = effective_pixel_to_user.transform_point(x + 0.5, y + 0.5)
                                color = paint.get_color(ux, uy)
                                buffer.set_pixel(x, y, color)
            else:
                # Nonzero: Use winding number logic
                cur_winding = 0
                for i in range(len(active_edges) - 1):
                    edge = active_edges[i]
                    next_edge = active_edges[i+1]
                    cur_winding += edge[3]  # Add effective direction
                    
                    should_fill = (cur_winding != 0)
                    
                    if should_fill:
                        # Fill run
                        x_start = max(0, int(edge[1] + 0.5))
                        x_end = min(buffer.width - 1, int(next_edge[1] + 0.5))
                        
                        if x_start <= x_end:
                             for x in range(x_start, x_end + 1):
                                # Sample paint with EFFECTIVE transform
                                ux, uy = effective_pixel_to_user.transform_point(x + 0.5, y + 0.5)
                                color = paint.get_color(ux, uy)
                                buffer.set_pixel(x, y, color)
            
            # Update x positions for next scanline
            for e in active_edges:
                e[1] += e[2]  # x += inv_slope

    def _render_text(self, buffer: PixelBuffer, text_element: Text, global_transform: Matrix, doc: SVGDocument):
        """Render text using Pillow."""
        if Image is None:
            return 
        
        text = text_element.text
        if not text:
            return
        
        font_size_str = str(text_element.font_size).replace('px', '').replace('pt', '').replace('em', '')
        try:
            font_size = int(float(font_size_str))
        except (ValueError, TypeError):
            font_size = 12
        
        scale = math.sqrt(global_transform.a**2 + global_transform.c**2)
        font_size = max(8, int(font_size * scale))
        
        # Resolve color
        paint = self._resolve_paint(text_element.style.fill, doc)
        color = (0, 0, 0, 255)
        if paint:
            # For gradients in text, just sample at center or use fallback. 
            # Supporting gradient text with Pillow mask is hard.
            # Just sample 0,0 for now or use solid color if it is one.
            if isinstance(paint, SolidColor):
                color = paint.color
            else:
                color = paint.get_color(0, 0) # Fallback sampling
        
        if color[3] == 0:
            return

        # Pillow rendering...
        temp_img = Image.new('RGBA', (buffer.width, buffer.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(temp_img)
        
        font = None
        # ... font loading logic ...
        try:
             font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
             font = ImageFont.load_default()

        x, y = text_element.x, text_element.y
        tx, ty = global_transform.transform_point(x, y)
        ty = ty - (font_size * 0.8)
        
        draw.text((tx, ty), text, font=font, fill=color)
        
        temp_pixels = temp_img.load()
        pixels_written = 0
        for py in range(buffer.height):
             for px in range(buffer.width):
                 r,g,b,a = temp_pixels[px,py]
                 if a > 0:
                     buffer.set_pixel(px, py, (r,g,b,a))
                     pixels_written += 1
