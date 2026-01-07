"""
Render Context for SVG compositing.

Manages the layer stack for handling opacity, masking, and blending.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from imgshift.svg.rasterizer import PixelBuffer
from imgshift.svg.transforms import Matrix

@dataclass
class Layer:
    """A rendering layer (intermediate buffer)."""
    buffer: PixelBuffer
    opacity: float = 1.0
    transform: Matrix = field(default_factory=Matrix.identity)
    # Mask buffer could be added here
    
    def blend_to(self, target: PixelBuffer):
        """Blend this layer onto the target buffer."""
        # This is a full-image blend with global opacity
        # Iterate over all pixels (slow in Python, but correct)
        # Optimization: use numpy or efficient blit if possible, for now reference loop
        
        # We use the existing blend logic per pixel but pre-multiply by layer opacity
        w, h = self.buffer.width, self.buffer.height
        
        for y in range(h):
            for x in range(w):
                idx = y * w + x
                # Source pixel
                sr, sg, sb, sa = self.buffer.pixels[idx]
                
                # Apply layer opacity
                final_alpha = int(sa * self.opacity)
                
                if final_alpha == 0:
                    continue
                    
                color = (sr, sg, sb, final_alpha)
                # target.set_pixel handles blending
                target.set_pixel(x, y, color)

class RenderContext:
    """Manages the stack of layers."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        # Base layer is the final output
        self.stack: List[Layer] = []
        
    def push_layer(self, opacity: float = 1.0):
        """Push a new transparent layer onto the stack."""
        # Create new clear buffer
        buffer = PixelBuffer(self.width, self.height, (0, 0, 0, 0))
        self.stack.append(Layer(buffer, opacity))
        
    def pop_layer(self, target: PixelBuffer):
        """Pop top layer and blend it onto the target (usually previous layer)."""
        if not self.stack:
            return
        
        layer = self.stack.pop()
        layer.blend_to(target)
        
    def get_current_buffer(self) -> PixelBuffer:
        """Get the buffer we should currently be drawing to."""
        if self.stack:
            return self.stack[-1].buffer
        raise Exception("No active layer!")
