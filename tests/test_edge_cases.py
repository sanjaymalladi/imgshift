"""
Comprehensive edge case tests for imgshift.

Tests various PNG types, image modes, and edge cases that could cause failures.
"""
import sys
sys.path.insert(0, "src")

import io
import tempfile
import urllib.request
from pathlib import Path
from PIL import Image as PILImage
import numpy as np

from imgshift import convert
from imgshift.formats.png import PNGHandler
from imgshift.formats.jpeg import JPEGHandler


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def success(self, name):
        self.passed += 1
        print(f"  ✓ {name}")
    
    def fail(self, name, error):
        self.failed += 1
        self.errors.append((name, error))
        print(f"  ✗ {name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Results: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print("\nFailed tests:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        return self.failed == 0


results = TestResults()
tmpdir = Path(tempfile.gettempdir()) / "imgshift_edge_cases"
tmpdir.mkdir(exist_ok=True)


def create_test_png(mode, size=(100, 100), filename=None):
    """Create a test PNG with specific mode using Pillow."""
    img = PILImage.new(mode, size)
    
    # For palette mode, we need to set up a palette FIRST
    if mode == 'P':
        # Create a 256-color palette (RGB values for each index)
        palette = [i % 256 for i in range(768)]  # 256 * 3 = 768 values
        img.putpalette(palette)
    
    # Fill with some pattern based on mode
    pixels = img.load()
    for y in range(size[1]):
        for x in range(size[0]):
            if mode == 'L':  # Greyscale
                pixels[x, y] = (x + y) % 256
            elif mode == 'LA':  # Greyscale + Alpha
                pixels[x, y] = ((x + y) % 256, 200)
            elif mode == 'P':  # Palette (set palette index)
                pixels[x, y] = (x * y) % 256
            elif mode == 'RGB':
                pixels[x, y] = ((x * 2) % 256, (y * 2) % 256, ((x + y) * 2) % 256)
            elif mode == 'RGBA':
                pixels[x, y] = ((x * 2) % 256, (y * 2) % 256, ((x + y) * 2) % 256, 200)
            elif mode == '1':  # 1-bit
                pixels[x, y] = (x + y) % 2
            elif mode == 'I':  # 32-bit integer
                pixels[x, y] = (x + y) * 100
            elif mode == 'F':  # 32-bit float
                pixels[x, y] = float((x + y) * 100)
    
    if filename is None:
        filename = tmpdir / f"test_{mode.lower()}.png"
    img.save(filename, 'PNG')
    return filename


def test_png_mode(mode, description):
    """Test reading a PNG with specific mode."""
    try:
        path = create_test_png(mode)
        rows, width, height = PNGHandler.read(path)
        assert len(rows) == 100, f"Expected 100 rows, got {len(rows)}"
        assert len(rows[0]) == 100, f"Expected 100 pixels per row, got {len(rows[0])}"
        assert len(rows[0][0]) == 4, f"Expected RGBA tuple, got {len(rows[0][0])} values"
        results.success(f"PNG mode {mode} ({description})")
        return True
    except Exception as e:
        results.fail(f"PNG mode {mode} ({description})", str(e))
        return False


def test_png_conversion(mode, target_format):
    """Test converting a PNG with specific mode to another format."""
    try:
        src_path = create_test_png(mode)
        dst_path = tmpdir / f"test_{mode.lower()}_to.{target_format}"
        convert(src_path, dst_path)
        assert dst_path.exists(), "Output file not created"
        assert dst_path.stat().st_size > 0, "Output file is empty"
        results.success(f"PNG {mode} -> {target_format.upper()}")
        return True
    except Exception as e:
        results.fail(f"PNG {mode} -> {target_format.upper()}", str(e))
        return False


def test_various_sizes():
    """Test various image sizes including edge cases."""
    sizes = [
        (1, 1),       # Minimum size
        (1, 100),     # Very narrow
        (100, 1),     # Very short
        (10, 10),     # Small
        (256, 256),   # Power of 2
        (257, 257),   # Non-power of 2
        (1000, 100),  # Wide
        (100, 1000),  # Tall
    ]
    
    print("\n--- Testing various image sizes ---")
    for size in sizes:
        try:
            path = create_test_png('RGBA', size)
            rows, width, height = PNGHandler.read(path)
            assert width == size[0], f"Width mismatch: {width} != {size[0]}"
            assert height == size[1], f"Height mismatch: {height} != {size[1]}"
            assert len(rows) == size[1], f"Row count mismatch"
            assert len(rows[0]) == size[0], f"Pixel count mismatch"
            results.success(f"Size {size[0]}x{size[1]}")
        except Exception as e:
            results.fail(f"Size {size[0]}x{size[1]}", str(e))


def test_bit_depths():
    """Test various bit depths."""
    print("\n--- Testing bit depths ---")
    
    # Create PNGs with different bit depths using raw pypng
    import png
    
    bit_depths = [1, 2, 4, 8, 16]
    for depth in bit_depths:
        try:
            # Create a simple greyscale image with specific bit depth
            max_val = (2 ** depth) - 1
            size = 10
            rows = [[int(max_val * x / size) for x in range(size)] for _ in range(size)]
            
            path = tmpdir / f"test_depth_{depth}.png"
            with open(path, 'wb') as f:
                writer = png.Writer(width=size, height=size, greyscale=True, bitdepth=depth)
                writer.write(f, rows)
            
            # Now read it back
            result_rows, width, height = PNGHandler.read(path)
            assert len(result_rows) == size
            results.success(f"Bit depth {depth}")
        except Exception as e:
            results.fail(f"Bit depth {depth}", str(e))


def test_transparency():
    """Test various transparency scenarios."""
    print("\n--- Testing transparency ---")
    
    # RGBA with full transparency
    try:
        img = PILImage.new('RGBA', (50, 50), (255, 0, 0, 0))
        path = tmpdir / "test_transparent.png"
        img.save(path)
        rows, w, h = PNGHandler.read(path)
        assert rows[0][0][3] == 0, "Alpha should be 0"
        results.success("Fully transparent RGBA")
    except Exception as e:
        results.fail("Fully transparent RGBA", str(e))
    
    # RGBA with partial transparency
    try:
        img = PILImage.new('RGBA', (50, 50), (255, 0, 0, 128))
        path = tmpdir / "test_semi_transparent.png"
        img.save(path)
        rows, w, h = PNGHandler.read(path)
        assert rows[0][0][3] == 128, f"Alpha should be 128, got {rows[0][0][3]}"
        results.success("Semi-transparent RGBA")
    except Exception as e:
        results.fail("Semi-transparent RGBA", str(e))
    
    # Palette with transparency (tRNS chunk)
    try:
        img = PILImage.new('P', (50, 50))
        # Set up a palette with transparency
        palette = [i % 256 for i in range(768)]  # RGB palette
        img.putpalette(palette)
        path = tmpdir / "test_palette_transparent.png"
        img.save(path, transparency=0)  # Index 0 is transparent
        rows, w, h = PNGHandler.read(path)
        results.success("Palette with transparency")
    except Exception as e:
        results.fail("Palette with transparency", str(e))


def test_interlaced_png():
    """Test interlaced (Adam7) PNG."""
    print("\n--- Testing interlaced PNG ---")
    try:
        import png
        size = 64
        rows = [[(x + y) % 256 for x in range(size)] for y in range(size)]
        
        path = tmpdir / "test_interlaced.png"
        with open(path, 'wb') as f:
            writer = png.Writer(width=size, height=size, greyscale=True, interlace=True)
            writer.write(f, rows)
        
        result_rows, width, height = PNGHandler.read(path)
        assert len(result_rows) == size
        results.success("Interlaced PNG (Adam7)")
    except Exception as e:
        results.fail("Interlaced PNG (Adam7)", str(e))


def test_real_world_pngs():
    """Test downloading and processing real-world PNGs."""
    print("\n--- Testing real-world PNGs ---")
    
    urls = [
        # GitHub logo (palette-indexed)
        ("https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png", "GitHub logo (palette)"),
        # Python logo (has transparency)
        ("https://www.python.org/static/community_logos/python-logo.png", "Python logo (transparent)"),
        # A simple PNG from httpbin
        ("https://httpbin.org/image/png", "httpbin PNG"),
    ]
    
    for url, description in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read()
            
            path = tmpdir / f"real_{description.replace(' ', '_').replace('(', '').replace(')', '')}.png"
            path.write_bytes(data)
            
            rows, width, height = PNGHandler.read(path)
            assert len(rows) > 0
            assert len(rows[0]) > 0
            
            # Also test conversion
            dst = tmpdir / f"real_{description.replace(' ', '_')}.jpg"
            convert(path, dst)
            assert dst.exists() and dst.stat().st_size > 0
            
            results.success(f"Real-world: {description}")
        except urllib.error.URLError as e:
            results.success(f"Real-world: {description} (skipped - network)")
        except Exception as e:
            results.fail(f"Real-world: {description}", str(e))


def test_grayscale_variants():
    """Test all grayscale variants."""
    print("\n--- Testing grayscale variants ---")
    
    import png
    
    # 8-bit grayscale
    try:
        size = 50
        rows = [[(x + y) % 256 for x in range(size)] for y in range(size)]
        path = tmpdir / "test_gray8.png"
        with open(path, 'wb') as f:
            writer = png.Writer(width=size, height=size, greyscale=True, bitdepth=8)
            writer.write(f, rows)
        result, w, h = PNGHandler.read(path)
        assert result[0][0][0] == result[0][0][1] == result[0][0][2], "Grayscale should have equal RGB"
        results.success("8-bit grayscale")
    except Exception as e:
        results.fail("8-bit grayscale", str(e))
    
    # 16-bit grayscale
    try:
        size = 50
        rows = [[(x + y) * 256 for x in range(size)] for y in range(size)]
        path = tmpdir / "test_gray16.png"
        with open(path, 'wb') as f:
            writer = png.Writer(width=size, height=size, greyscale=True, bitdepth=16)
            writer.write(f, rows)
        result, w, h = PNGHandler.read(path)
        results.success("16-bit grayscale")
    except Exception as e:
        results.fail("16-bit grayscale", str(e))
    
    # Grayscale with alpha
    try:
        size = 50
        rows = []
        for y in range(size):
            row = []
            for x in range(size):
                row.extend([(x + y) % 256, 200])  # Gray, Alpha
            rows.append(row)
        path = tmpdir / "test_gray_alpha.png"
        with open(path, 'wb') as f:
            writer = png.Writer(width=size, height=size, greyscale=True, alpha=True, bitdepth=8)
            writer.write(f, rows)
        result, w, h = PNGHandler.read(path)
        results.success("Grayscale with alpha")
    except Exception as e:
        results.fail("Grayscale with alpha", str(e))


def test_file_like_objects():
    """Test reading from file-like objects (BytesIO)."""
    print("\n--- Testing file-like objects ---")
    
    try:
        # Create a PNG in memory
        img = PILImage.new('RGBA', (50, 50), (255, 128, 64, 200))
        buffer = io.BytesIO()
        img.save(buffer, 'PNG')
        buffer.seek(0)
        
        rows, width, height = PNGHandler.read(buffer)
        assert width == 50 and height == 50
        results.success("Read from BytesIO")
    except Exception as e:
        results.fail("Read from BytesIO", str(e))
    
    try:
        # Write to BytesIO
        rows = [[(255, 128, 64, 200) for _ in range(50)] for _ in range(50)]
        buffer = io.BytesIO()
        PNGHandler.write(buffer, rows)
        buffer.seek(0)
        assert len(buffer.read()) > 0
        results.success("Write to BytesIO")
    except Exception as e:
        results.fail("Write to BytesIO", str(e))


def test_format_conversions():
    """Test various format conversion combinations."""
    print("\n--- Testing format conversions ---")
    
    formats = ['png', 'jpg', 'bmp', 'gif', 'webp']
    
    # Create a source image
    src_img = PILImage.new('RGBA', (100, 100), (255, 128, 64, 200))
    for y in range(100):
        for x in range(100):
            src_img.putpixel((x, y), ((x * 2) % 256, (y * 2) % 256, ((x + y) * 2) % 256, 200))
    
    src_path = tmpdir / "conversion_source.png"
    src_img.save(src_path)
    
    for target_fmt in formats:
        try:
            dst_path = tmpdir / f"conversion_target.{target_fmt}"
            convert(src_path, dst_path)
            assert dst_path.exists(), f"Output {target_fmt} not created"
            assert dst_path.stat().st_size > 0, f"Output {target_fmt} is empty"
            
            # Verify the output is valid by opening it
            result = PILImage.open(dst_path)
            assert result.size == (100, 100), f"Size mismatch for {target_fmt}"
            
            results.success(f"PNG -> {target_fmt.upper()}")
        except Exception as e:
            results.fail(f"PNG -> {target_fmt.upper()}", str(e))


def test_corrupted_handling():
    """Test handling of corrupted/invalid files."""
    print("\n--- Testing error handling ---")
    
    # Empty file
    try:
        path = tmpdir / "empty.png"
        path.write_bytes(b'')
        PNGHandler.read(path)
        results.fail("Empty file", "Should have raised an error")
    except Exception:
        results.success("Empty file (correctly rejected)")
    
    # Random bytes
    try:
        path = tmpdir / "random.png"
        path.write_bytes(b'\x89PNG\r\n\x1a\n' + b'garbage' * 100)
        PNGHandler.read(path)
        results.fail("Corrupted PNG", "Should have raised an error")
    except Exception:
        results.success("Corrupted PNG (correctly rejected)")
    
    # JPEG with .png extension
    try:
        img = PILImage.new('RGB', (50, 50), (255, 0, 0))
        path = tmpdir / "fake.png"
        img.save(path, 'JPEG')  # Save as JPEG but with .png extension
        PNGHandler.read(path)
        results.fail("JPEG as PNG", "Should have raised an error")
    except Exception:
        results.success("JPEG as PNG (correctly rejected)")


def test_special_colors():
    """Test special color values."""
    print("\n--- Testing special colors ---")
    
    # All black
    try:
        img = PILImage.new('RGBA', (50, 50), (0, 0, 0, 255))
        path = tmpdir / "all_black.png"
        img.save(path)
        rows, w, h = PNGHandler.read(path)
        assert rows[0][0] == (0, 0, 0, 255)
        results.success("All black image")
    except Exception as e:
        results.fail("All black image", str(e))
    
    # All white
    try:
        img = PILImage.new('RGBA', (50, 50), (255, 255, 255, 255))
        path = tmpdir / "all_white.png"
        img.save(path)
        rows, w, h = PNGHandler.read(path)
        assert rows[0][0] == (255, 255, 255, 255)
        results.success("All white image")
    except Exception as e:
        results.fail("All white image", str(e))
    
    # Gradient
    try:
        img = PILImage.new('L', (256, 1))
        for x in range(256):
            img.putpixel((x, 0), x)
        path = tmpdir / "gradient.png"
        img.save(path)
        rows, w, h = PNGHandler.read(path)
        # Check gradient preserved
        for i in range(256):
            assert rows[0][i][0] == i, f"Gradient broken at {i}"
        results.success("Grayscale gradient")
    except Exception as e:
        results.fail("Grayscale gradient", str(e))


if __name__ == "__main__":
    print("=" * 60)
    print("IMGSHIFT EDGE CASE TESTS")
    print("=" * 60)
    print(f"Temp directory: {tmpdir}")
    
    # Test PNG modes
    print("\n--- Testing PNG color modes ---")
    test_png_mode('L', 'Greyscale 8-bit')
    test_png_mode('LA', 'Greyscale + Alpha')
    test_png_mode('P', 'Palette-indexed')
    test_png_mode('RGB', 'RGB 24-bit')
    test_png_mode('RGBA', 'RGBA 32-bit')
    test_png_mode('1', '1-bit black/white')
    
    # Test sizes
    test_various_sizes()
    
    # Test bit depths
    test_bit_depths()
    
    # Test transparency
    test_transparency()
    
    # Test interlaced
    test_interlaced_png()
    
    # Test grayscale variants
    test_grayscale_variants()
    
    # Test file-like objects
    test_file_like_objects()
    
    # Test format conversions
    test_format_conversions()
    
    # Test special colors
    test_special_colors()
    
    # Test error handling
    test_corrupted_handling()
    
    # Test real-world images (network required)
    test_real_world_pngs()
    
    # Summary
    success = results.summary()
    sys.exit(0 if success else 1)
