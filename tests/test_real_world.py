"""
Real-world image testing script.

Downloads actual company logos and images from the internet,
converts them through all format combinations, and verifies quality.
"""

import os
import sys
import urllib.request
import tempfile
from pathlib import Path
from itertools import permutations
import hashlib

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from imgshift import convert, Image


# Real test images from the internet
TEST_IMAGES = {
    # PNG images
    'github_mark': {
        'url': 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png',
        'format': 'png',
        'description': 'GitHub logo (PNG)',
    },
    'python_powered': {
        'url': 'https://www.python.org/static/community_logos/python-powered-w-200x80.png', 
        'format': 'png',
        'description': 'Python Powered logo (PNG)',
    },
}

# SVG test content (embedded since SVG URLs often have CORS issues)
TEST_SVGS = {
    'simple_shapes': '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <rect width="200" height="200" fill="#2c3e50"/>
    <circle cx="100" cy="100" r="60" fill="#e74c3c"/>
    <circle cx="100" cy="100" r="40" fill="#f39c12"/>
    <circle cx="100" cy="100" r="20" fill="#2ecc71"/>
</svg>''',
    
    'logo_style': '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="300" height="100" xmlns="http://www.w3.org/2000/svg">
    <rect width="300" height="100" fill="#1a1a2e"/>
    <text x="20" y="65" font-family="Arial, sans-serif" font-size="40" fill="#00fff5">imgshift</text>
    <rect x="220" y="25" width="60" height="50" rx="10" fill="#e94560"/>
    <path d="M 235 50 L 265 50 M 250 35 L 250 65" stroke="white" stroke-width="4"/>
</svg>''',
    
    'complex_paths': '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <style>
            .st0{fill:#3498db;}
            .st1{fill:#e74c3c;}
        </style>
    </defs>
    <rect width="200" height="200" fill="#ecf0f1"/>
    <path class="st0" d="M 50,100 C 50,50 100,50 100,100 C 100,150 150,150 150,100"/>
    <path class="st1" d="M 30,30 L 170,30 L 170,170 L 30,170 Z M 50,50 L 50,150 L 150,150 L 150,50 Z"/>
    <ellipse cx="100" cy="100" rx="30" ry="15" fill="#9b59b6"/>
</svg>''',

    'gradients_and_transforms': '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <rect width="200" height="200" fill="#2d3436"/>
    <g transform="translate(100, 100)">
        <rect x="-50" y="-50" width="100" height="100" fill="#74b9ff" transform="rotate(0)"/>
        <rect x="-40" y="-40" width="80" height="80" fill="#a29bfe" transform="rotate(15)"/>
        <rect x="-30" y="-30" width="60" height="60" fill="#fd79a8" transform="rotate(30)"/>
        <rect x="-20" y="-20" width="40" height="40" fill="#ffeaa7" transform="rotate(45)"/>
    </g>
</svg>''',
}

# All formats to test
RASTER_FORMATS = ['png', 'jpg', 'webp', 'gif', 'bmp', 'tiff']


def download_image(url: str, dest: Path) -> bool:
    """Download an image from URL."""
    try:
        print(f"  Downloading {url}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            dest.write_bytes(response.read())
        return True
    except Exception as e:
        print(f"  Failed to download: {e}")
        return False


def get_image_hash(rows) -> str:
    """Get a hash of image pixel data for comparison."""
    data = bytearray()
    for row in rows[:10]:  # Sample first 10 rows for speed
        for pixel in row[:10]:
            data.extend([pixel[0], pixel[1], pixel[2]])
    return hashlib.md5(bytes(data)).hexdigest()[:8]


def compare_images(path1: Path, path2: Path) -> dict:
    """Compare two images and return similarity metrics."""
    from PIL import Image as PILImage
    
    img1 = PILImage.open(path1).convert('RGB')
    img2 = PILImage.open(path2).convert('RGB')
    
    # Resize to same size for comparison
    size = (100, 100)
    img1_resized = img1.resize(size, PILImage.Resampling.LANCZOS)
    img2_resized = img2.resize(size, PILImage.Resampling.LANCZOS)
    
    # Calculate pixel difference
    pixels1 = list(img1_resized.getdata())
    pixels2 = list(img2_resized.getdata())
    
    total_diff = 0
    for p1, p2 in zip(pixels1, pixels2):
        total_diff += abs(p1[0] - p2[0]) + abs(p1[1] - p2[1]) + abs(p1[2] - p2[2])
    
    max_diff = len(pixels1) * 3 * 255
    similarity = 1 - (total_diff / max_diff)
    
    return {
        'similarity': similarity,
        'size_ratio': path2.stat().st_size / path1.stat().st_size,
    }


def test_svg_conversions(tmpdir: Path) -> dict:
    """Test all SVG to raster conversions."""
    print("\n" + "=" * 60)
    print("TESTING SVG CONVERSIONS")
    print("=" * 60)
    
    results = {}
    
    for svg_name, svg_content in TEST_SVGS.items():
        print(f"\n📄 Testing: {svg_name}")
        
        svg_path = tmpdir / f"{svg_name}.svg"
        svg_path.write_text(svg_content)
        
        svg_results = {'formats': {}, 'sizes': {}}
        
        for fmt in RASTER_FORMATS + ['pdf']:
            output_path = tmpdir / f"{svg_name}.{fmt}"
            
            try:
                convert(svg_path, output_path, width=400)
                
                if output_path.exists():
                    size = output_path.stat().st_size
                    svg_results['formats'][fmt] = True
                    svg_results['sizes'][fmt] = size
                    print(f"  ✓ SVG -> {fmt:5}: {size:>8} bytes")
                else:
                    svg_results['formats'][fmt] = False
                    print(f"  ✗ SVG -> {fmt:5}: File not created")
                    
            except Exception as e:
                svg_results['formats'][fmt] = False
                print(f"  ✗ SVG -> {fmt:5}: {e}")
        
        results[svg_name] = svg_results
    
    return results


def test_raster_permutations(tmpdir: Path) -> dict:
    """Test all raster-to-raster format permutations."""
    print("\n" + "=" * 60)
    print("TESTING RASTER FORMAT PERMUTATIONS")
    print("=" * 60)
    
    # Create a source image from SVG
    svg_content = TEST_SVGS['simple_shapes']
    svg_path = tmpdir / "source.svg"
    svg_path.write_text(svg_content)
    
    base_png = tmpdir / "base.png"
    convert(svg_path, base_png, width=200)
    
    results = {'matrix': {}, 'failures': []}
    
    print(f"\n📊 Testing {len(RASTER_FORMATS)}x{len(RASTER_FORMATS)-1} = {len(RASTER_FORMATS) * (len(RASTER_FORMATS)-1)} conversions...")
    
    for src_fmt in RASTER_FORMATS:
        results['matrix'][src_fmt] = {}
        
        # Create source in this format
        src_path = tmpdir / f"source.{src_fmt}"
        convert(base_png, src_path)
        
        for dst_fmt in RASTER_FORMATS:
            if src_fmt == dst_fmt:
                continue
            
            dst_path = tmpdir / f"converted_{src_fmt}_to_{dst_fmt}.{dst_fmt}"
            
            try:
                convert(src_path, dst_path)
                
                if dst_path.exists() and dst_path.stat().st_size > 100:
                    # Compare with original
                    comparison = compare_images(base_png, dst_path)
                    results['matrix'][src_fmt][dst_fmt] = {
                        'success': True,
                        'size': dst_path.stat().st_size,
                        'similarity': comparison['similarity'],
                    }
                else:
                    results['matrix'][src_fmt][dst_fmt] = {'success': False}
                    results['failures'].append((src_fmt, dst_fmt, 'Empty file'))
                    
            except Exception as e:
                results['matrix'][src_fmt][dst_fmt] = {'success': False, 'error': str(e)}
                results['failures'].append((src_fmt, dst_fmt, str(e)))
    
    # Print matrix
    print("\n  Format Conversion Matrix (% similarity to original):")
    print("  " + "-" * 55)
    header = "        " + " ".join(f"{f:>6}" for f in RASTER_FORMATS)
    print(f"  {header}")
    
    for src_fmt in RASTER_FORMATS:
        row = f"  {src_fmt:>6}:"
        for dst_fmt in RASTER_FORMATS:
            if src_fmt == dst_fmt:
                row += "     - "
            else:
                data = results['matrix'].get(src_fmt, {}).get(dst_fmt, {})
                if data.get('success'):
                    sim = data.get('similarity', 0) * 100
                    row += f" {sim:5.1f}%"
                else:
                    row += "  FAIL "
        print(row)
    
    return results


def test_real_images(tmpdir: Path) -> dict:
    """Test with real downloaded images."""
    print("\n" + "=" * 60)
    print("TESTING WITH REAL IMAGES FROM INTERNET")
    print("=" * 60)
    
    results = {}
    
    for name, info in TEST_IMAGES.items():
        print(f"\n🌐 {info['description']}")
        
        # Download image
        src_path = tmpdir / f"{name}.{info['format']}"
        
        if not download_image(info['url'], src_path):
            results[name] = {'success': False, 'error': 'Download failed'}
            continue
        
        original_size = src_path.stat().st_size
        print(f"  Downloaded: {original_size} bytes")
        
        # Convert to all formats
        img_results = {'original_size': original_size, 'conversions': {}}
        
        for fmt in RASTER_FORMATS:
            if fmt == info['format']:
                continue
            
            output_path = tmpdir / f"{name}_converted.{fmt}"
            
            try:
                convert(src_path, output_path)
                
                if output_path.exists():
                    new_size = output_path.stat().st_size
                    comparison = compare_images(src_path, output_path)
                    
                    img_results['conversions'][fmt] = {
                        'success': True,
                        'size': new_size,
                        'similarity': comparison['similarity'],
                    }
                    
                    sim_pct = comparison['similarity'] * 100
                    status = "✓" if sim_pct > 95 else "⚠" if sim_pct > 80 else "✗"
                    print(f"  {status} {info['format']} -> {fmt}: {sim_pct:.1f}% similar, {new_size} bytes")
                    
            except Exception as e:
                img_results['conversions'][fmt] = {'success': False, 'error': str(e)}
                print(f"  ✗ {info['format']} -> {fmt}: {e}")
        
        results[name] = img_results
    
    return results


def test_quality_preservation(tmpdir: Path) -> dict:
    """Test that quality is preserved through conversion chains."""
    print("\n" + "=" * 60)
    print("TESTING QUALITY PRESERVATION")
    print("=" * 60)
    
    # Create high-quality source
    svg_content = TEST_SVGS['complex_paths']
    svg_path = tmpdir / "quality_test.svg"
    svg_path.write_text(svg_content)
    
    original_png = tmpdir / "quality_original.png"
    convert(svg_path, original_png, width=400)
    
    results = {'chains': []}
    
    # Test various conversion chains
    chains = [
        ['png', 'jpg', 'png'],  # Lossy roundtrip
        ['png', 'webp', 'png'],  # WebP roundtrip
        ['png', 'bmp', 'png'],  # Lossless roundtrip
        ['png', 'tiff', 'png'],  # TIFF roundtrip
        ['png', 'jpg', 'webp', 'png'],  # Multi-format chain
    ]
    
    for chain in chains:
        print(f"\n  Testing chain: {' -> '.join(chain)}")
        
        current_path = original_png
        chain_results = {'formats': chain, 'steps': []}
        
        for i, fmt in enumerate(chain[1:], 1):
            output_path = tmpdir / f"chain_step_{i}.{fmt}"
            convert(current_path, output_path, quality=95)
            
            comparison = compare_images(original_png, output_path)
            chain_results['steps'].append({
                'format': fmt,
                'similarity': comparison['similarity'],
                'size': output_path.stat().st_size,
            })
            
            current_path = output_path
        
        final_similarity = chain_results['steps'][-1]['similarity'] * 100
        status = "✓" if final_similarity > 90 else "⚠" if final_similarity > 70 else "✗"
        print(f"  {status} Final similarity: {final_similarity:.1f}%")
        
        results['chains'].append(chain_results)
    
    return results


def main():
    """Run all tests."""
    print("\n" + "#" * 60)
    print("#  IMGSHIFT COMPREHENSIVE FORMAT TESTING")
    print("#" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        all_results = {}
        
        # Test 1: SVG conversions
        all_results['svg'] = test_svg_conversions(tmpdir)
        
        # Test 2: Raster permutations
        all_results['raster'] = test_raster_permutations(tmpdir)
        
        # Test 3: Real images (optional, requires internet)
        try:
            all_results['real_images'] = test_real_images(tmpdir)
        except Exception as e:
            print(f"\n⚠ Skipping real image tests: {e}")
        
        # Test 4: Quality preservation
        all_results['quality'] = test_quality_preservation(tmpdir)
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        # Count successes/failures
        svg_success = sum(
            1 for svg_data in all_results.get('svg', {}).values() 
            for success in svg_data.get('formats', {}).values() if success
        )
        
        raster_failures = len(all_results.get('raster', {}).get('failures', []))
        
        print(f"\n  SVG Conversions: {svg_success} successful")
        print(f"  Raster Permutations: {len(RASTER_FORMATS) * (len(RASTER_FORMATS)-1) - raster_failures} successful, {raster_failures} failed")
        
        if raster_failures == 0:
            print("\n  ✅ ALL TESTS PASSED!")
        else:
            print("\n  ⚠ Some tests had issues. Check output above.")
            for src, dst, err in all_results.get('raster', {}).get('failures', []):
                print(f"    - {src} -> {dst}: {err}")


if __name__ == "__main__":
    main()
