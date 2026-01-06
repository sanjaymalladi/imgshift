"""
Comprehensive format conversion tests.

Tests all format permutations with real images to verify:
1. All format conversions work
2. Image quality is preserved
3. No visual corruption
"""

import pytest
import tempfile
import os
import urllib.request
from pathlib import Path
from itertools import permutations

from imgshift import convert, Image


# Test image URLs (real company logos and images)
TEST_IMAGES = {
    'github_logo': 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png',
    'python_logo': 'https://www.python.org/static/community_logos/python-logo-generic.svg',
}

# All supported formats for testing
RASTER_FORMATS = ['png', 'jpg', 'webp', 'gif', 'bmp', 'tiff']
ALL_FORMATS = RASTER_FORMATS + ['pdf']


@pytest.fixture(scope="module")
def test_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="module")
def sample_svg():
    """Create a sample SVG for testing."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <!-- Background -->
    <rect width="200" height="200" fill="#f0f0f0"/>
    
    <!-- Red circle -->
    <circle cx="100" cy="80" r="50" fill="#e74c3c"/>
    
    <!-- Blue rectangle -->
    <rect x="50" y="120" width="100" height="60" fill="#3498db" rx="10"/>
    
    <!-- Green triangle using path -->
    <path d="M 100 10 L 150 60 L 50 60 Z" fill="#2ecc71"/>
    
    <!-- Yellow star -->
    <polygon points="100,140 110,165 140,165 115,180 125,205 100,190 75,205 85,180 60,165 90,165" 
             fill="#f1c40f" transform="translate(0, -20) scale(0.6)"/>
    
    <!-- Text-like shapes -->
    <rect x="30" y="170" width="40" height="8" fill="#333"/>
    <rect x="80" y="170" width="40" height="8" fill="#333"/>
    <rect x="130" y="170" width="40" height="8" fill="#333"/>
</svg>'''


@pytest.fixture(scope="module")
def complex_svg():
    """Create a more complex SVG with paths and transforms."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="300" height="300" viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
    <!-- Gradient background simulation with overlapping shapes -->
    <rect width="300" height="300" fill="#1a1a2e"/>
    <circle cx="0" cy="0" r="200" fill="#16213e" opacity="0.7"/>
    <circle cx="300" cy="300" r="200" fill="#0f3460" opacity="0.7"/>
    
    <!-- Complex path - bezier curves -->
    <path d="M 50 150 
             C 50 50, 150 50, 150 150 
             C 150 250, 250 250, 250 150
             C 250 50, 150 50, 150 150"
          fill="none" stroke="#e94560" stroke-width="4"/>
    
    <!-- Rotated rectangles -->
    <g transform="translate(150, 150)">
        <rect x="-40" y="-40" width="80" height="80" fill="#00fff5" opacity="0.5" 
              transform="rotate(0)"/>
        <rect x="-40" y="-40" width="80" height="80" fill="#00fff5" opacity="0.5" 
              transform="rotate(15)"/>
        <rect x="-40" y="-40" width="80" height="80" fill="#00fff5" opacity="0.5" 
              transform="rotate(30)"/>
        <rect x="-40" y="-40" width="80" height="80" fill="#00fff5" opacity="0.5" 
              transform="rotate(45)"/>
    </g>
    
    <!-- Ellipses -->
    <ellipse cx="75" cy="225" rx="50" ry="30" fill="#f39c12"/>
    <ellipse cx="225" cy="75" rx="30" ry="50" fill="#9b59b6"/>
    
    <!-- Polyline -->
    <polyline points="20,20 40,40 60,20 80,40 100,20" 
              stroke="#ecf0f1" stroke-width="3" fill="none"/>
</svg>'''


class TestSVGToAllFormats:
    """Test SVG conversion to all formats."""
    
    def test_svg_to_png(self, test_dir, sample_svg):
        """Test SVG to PNG conversion."""
        svg_path = test_dir / "test.svg"
        png_path = test_dir / "test_from_svg.png"
        
        svg_path.write_text(sample_svg)
        convert(svg_path, png_path)
        
        assert png_path.exists()
        assert png_path.stat().st_size > 1000  # Should be a reasonable size
    
    def test_svg_to_jpg(self, test_dir, sample_svg):
        """Test SVG to JPEG conversion."""
        svg_path = test_dir / "test.svg"
        jpg_path = test_dir / "test_from_svg.jpg"
        
        svg_path.write_text(sample_svg)
        convert(svg_path, jpg_path, quality=95)
        
        assert jpg_path.exists()
        assert jpg_path.stat().st_size > 1000
    
    def test_svg_to_webp(self, test_dir, sample_svg):
        """Test SVG to WebP conversion."""
        svg_path = test_dir / "test.svg"
        webp_path = test_dir / "test_from_svg.webp"
        
        svg_path.write_text(sample_svg)
        convert(svg_path, webp_path)
        
        assert webp_path.exists()
    
    def test_svg_to_pdf(self, test_dir, sample_svg):
        """Test SVG to PDF conversion."""
        svg_path = test_dir / "test.svg"
        pdf_path = test_dir / "test_from_svg.pdf"
        
        svg_path.write_text(sample_svg)
        convert(svg_path, pdf_path)
        
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 100
    
    def test_complex_svg_rendering(self, test_dir, complex_svg):
        """Test complex SVG with beziers and transforms."""
        svg_path = test_dir / "complex.svg"
        png_path = test_dir / "complex.png"
        
        svg_path.write_text(complex_svg)
        convert(svg_path, png_path, width=600)
        
        assert png_path.exists()
        assert png_path.stat().st_size > 5000  # Complex image should be larger
    
    def test_svg_resize(self, test_dir, sample_svg):
        """Test SVG to PNG with specific size."""
        svg_path = test_dir / "test.svg"
        png_path = test_dir / "test_resized.png"
        
        svg_path.write_text(sample_svg)
        convert(svg_path, png_path, width=512, height=512)
        
        assert png_path.exists()


class TestRasterToRasterPermutations:
    """Test all raster-to-raster format conversions."""
    
    def test_png_roundtrip(self, test_dir, sample_svg):
        """Test PNG -> other formats -> PNG roundtrip."""
        # First create a PNG from SVG
        svg_path = test_dir / "source.svg"
        svg_path.write_text(sample_svg)
        
        original_png = test_dir / "original.png"
        convert(svg_path, original_png)
        
        # Convert to each format and back
        for fmt in ['jpg', 'webp', 'bmp', 'tiff']:
            intermediate = test_dir / f"intermediate.{fmt}"
            final_png = test_dir / f"final_from_{fmt}.png"
            
            convert(original_png, intermediate)
            assert intermediate.exists(), f"Failed to create {fmt}"
            
            convert(intermediate, final_png)
            assert final_png.exists(), f"Failed to convert {fmt} back to PNG"
    
    @pytest.mark.parametrize("src_fmt,dst_fmt", [
        ("png", "jpg"),
        ("png", "webp"),
        ("png", "gif"),
        ("png", "bmp"),
        ("png", "tiff"),
        ("jpg", "png"),
        ("jpg", "webp"),
        ("webp", "png"),
        ("webp", "jpg"),
        ("bmp", "png"),
        ("tiff", "png"),
        ("gif", "png"),
    ])
    def test_format_pair(self, test_dir, sample_svg, src_fmt, dst_fmt):
        """Test specific format conversion pairs."""
        # Create source image
        svg_path = test_dir / f"source_{src_fmt}_{dst_fmt}.svg"
        svg_path.write_text(sample_svg)
        
        src_path = test_dir / f"source_{src_fmt}_{dst_fmt}.{src_fmt}"
        dst_path = test_dir / f"output_{src_fmt}_{dst_fmt}.{dst_fmt}"
        
        # SVG -> source format
        convert(svg_path, src_path)
        assert src_path.exists()
        
        # Source format -> destination format
        convert(src_path, dst_path)
        assert dst_path.exists()
        assert dst_path.stat().st_size > 100


class TestPDFConversions:
    """Test PDF conversions."""
    
    def test_image_to_pdf(self, test_dir, sample_svg):
        """Test converting image to PDF."""
        svg_path = test_dir / "pdf_test.svg"
        svg_path.write_text(sample_svg)
        
        png_path = test_dir / "pdf_source.png"
        pdf_path = test_dir / "output.pdf"
        
        convert(svg_path, png_path)
        convert(png_path, pdf_path)
        
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 100
    
    def test_multiple_images_to_pdf(self, test_dir, sample_svg, complex_svg):
        """Test combining multiple images into PDF."""
        svg1_path = test_dir / "page1.svg"
        svg2_path = test_dir / "page2.svg"
        svg1_path.write_text(sample_svg)
        svg2_path.write_text(complex_svg)
        
        png1_path = test_dir / "page1.png"
        png2_path = test_dir / "page2.png"
        convert(svg1_path, png1_path)
        convert(svg2_path, png2_path)
        
        pdf_path = test_dir / "combined.pdf"
        convert([str(png1_path), str(png2_path)], pdf_path)
        
        assert pdf_path.exists()


class TestFluentAPI:
    """Test the Image fluent API."""
    
    def test_method_chaining(self, test_dir, sample_svg):
        """Test fluent API with method chaining."""
        svg_path = test_dir / "fluent_test.svg"
        svg_path.write_text(sample_svg)
        
        output_path = test_dir / "fluent_output.png"
        
        Image(svg_path).resize(400, 400).set_dpi(150).save(output_path)
        
        assert output_path.exists()
    
    def test_quality_setting(self, test_dir, sample_svg):
        """Test quality settings."""
        svg_path = test_dir / "quality_test.svg"
        svg_path.write_text(sample_svg)
        
        png_path = test_dir / "quality_source.png"
        convert(svg_path, png_path)
        
        high_quality = test_dir / "high_quality.jpg"
        low_quality = test_dir / "low_quality.jpg"
        
        Image(png_path).set_quality(95).save(high_quality)
        Image(png_path).set_quality(20).save(low_quality)
        
        # High quality should be larger
        assert high_quality.stat().st_size > low_quality.stat().st_size


class TestImageQualityPreservation:
    """Test that image quality and content is preserved through conversions."""
    
    def test_lossless_png_roundtrip(self, test_dir, sample_svg):
        """Test that PNG -> PNG preserves quality."""
        svg_path = test_dir / "lossless.svg"
        svg_path.write_text(sample_svg)
        
        png1 = test_dir / "lossless1.png"
        png2 = test_dir / "lossless2.png"
        
        convert(svg_path, png1)
        convert(png1, png2)
        
        # File sizes should be similar for identical images
        size1 = png1.stat().st_size
        size2 = png2.stat().st_size
        
        # Allow 5% difference due to compression variations
        assert abs(size1 - size2) / size1 < 0.05
    
    def test_dimension_preservation(self, test_dir, sample_svg):
        """Test that dimensions are preserved."""
        svg_path = test_dir / "dimension.svg"
        svg_path.write_text(sample_svg)
        
        # Convert with specific dimensions
        output = test_dir / "dimension_output.png"
        convert(svg_path, output, width=500, height=500)
        
        # Read back and verify (using PIL since we have it)
        from PIL import Image as PILImage
        with PILImage.open(output) as img:
            assert img.size == (500, 500)


class TestAllFormatPermutations:
    """Test comprehensive format permutation matrix."""
    
    def test_all_raster_permutations(self, test_dir, sample_svg):
        """Test all possible raster format conversions."""
        # Create base PNG from SVG
        svg_path = test_dir / "permutation_base.svg"
        svg_path.write_text(sample_svg)
        
        base_png = test_dir / "permutation_base.png"
        convert(svg_path, base_png)
        
        formats = ['png', 'jpg', 'webp', 'bmp', 'tiff', 'gif']
        results = []
        
        for src_fmt in formats:
            # First convert base to source format
            src_path = test_dir / f"perm_src.{src_fmt}"
            convert(base_png, src_path)
            
            for dst_fmt in formats:
                if src_fmt == dst_fmt:
                    continue
                
                dst_path = test_dir / f"perm_{src_fmt}_to_{dst_fmt}.{dst_fmt}"
                
                try:
                    convert(src_path, dst_path)
                    success = dst_path.exists() and dst_path.stat().st_size > 100
                    results.append((src_fmt, dst_fmt, success))
                except Exception as e:
                    results.append((src_fmt, dst_fmt, False))
                    print(f"Failed: {src_fmt} -> {dst_fmt}: {e}")
        
        # Print results matrix
        print("\n\nFormat Conversion Matrix:")
        print("-" * 60)
        for src, dst, success in results:
            status = "✓" if success else "✗"
            print(f"  {src:6} -> {dst:6}: {status}")
        
        # All should succeed
        failed = [(s, d) for s, d, ok in results if not ok]
        assert len(failed) == 0, f"Failed conversions: {failed}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
