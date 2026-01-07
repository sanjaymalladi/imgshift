import os
import urllib.request
from pathlib import Path
from glob import glob
from imgshift.core import Image

# Ensure the output directory exists
OUTPUT_DIR = Path(__file__).parent / "data" / "repro"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = OUTPUT_DIR / "repro_log.txt"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(str(msg) + "\n")

# Sample SVGs to generate locally
LOCAL_SVGS = {
    "rect.svg": """
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect x="50" y="50" width="100" height="100" fill="red" stroke="black" stroke-width="5"/>
</svg>
""",
    "circle.svg": """
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <circle cx="100" cy="100" r="50" fill="blue" stroke="green" stroke-width="5"/>
</svg>
""",
    "text.svg": """
<svg width="300" height="100" xmlns="http://www.w3.org/2000/svg">
  <text x="10" y="50" font-family="Arial" font-size="40" fill="black">Hello SVG</text>
</svg>
""",
    "complex_path.svg": """
<svg width="200" height="200" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <path d="M10 10 H 90 V 90 H 10 L 10 10" fill="none" stroke="purple" stroke-width="2"/>
  <path d="M50 10 Q 90 50 50 90 T 50 10" fill="yellow" stroke="orange" stroke-width="2"/>
</svg>
"""
}

# External SVG URLs
EXTERNAL_SVGS = [
    # simple-icons (converted to raw URLs)
    "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/github.svg",
    "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/python.svg",
    "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/instagram.svg",
    "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/facebook.svg",
    "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/google.svg",
    # devicon
    "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/html5/html5-original.svg",
    "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/css3/css3-original.svg",
    "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/javascript/javascript-original.svg",
    "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/react/react-original.svg",
    "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/nodejs/nodejs-original.svg",
    # lottosport
    "https://lottosport.in/cdn/shop/files/logo.svg?v=1742905730"
]

def create_local_svgs():
    """Create local sample SVG files."""
    print(f"Creating sample SVGs in {OUTPUT_DIR}...")
    for filename, content in LOCAL_SVGS.items():
        file_path = OUTPUT_DIR / filename
        with open(file_path, "w") as f:
            f.write(content.strip())
        print(f"  Created {filename}")

def download_external_svgs():
    """Download external SVG files."""
    print("Downloading external SVGs...")
    for url in EXTERNAL_SVGS:
        # Extract filename, removing query parameters
        clean_url = url.split("?")[0]
        filename = clean_url.split("/")[-1]
        
        # Handle duplicates or specific naming
        if "simple-icons" in url:
            filename = f"simple_icon_{filename}"
        elif "devicon" in url:
            filename = f"devicon_{filename}"
        elif "lottosport.in" in url:
            filename = f"lottosport_{filename}"
            
        file_path = OUTPUT_DIR / filename
        print(f"  Downloading {url} to {filename}...")
        try:
            # Use a proper user agent to avoid 403s on some sites
            req = urllib.request.Request(
                url, 
                data=None, 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            with urllib.request.urlopen(req) as response, open(file_path, 'wb') as out_file:
                data = response.read()
                out_file.write(data)
        except Exception as e:
            print(f"  Failed to download {url}: {e}")

def convert_svgs():
    """Convert all SVGs in the output directory using the engine dispatcher (auto mode)."""
    print("Converting SVGs with auto engine (resvg if available, fallback to Python)...")
    svg_files = list(OUTPUT_DIR.glob("*.svg"))
    
    from imgshift import convert
    
    for src_path in svg_files:
        filename = src_path.name
        base_name = src_path.stem
        png_path = OUTPUT_DIR / f"{base_name}.png"
        jpg_path = OUTPUT_DIR / f"{base_name}.jpg"
        webp_path = OUTPUT_DIR / f"{base_name}.webp"
        
        print(f"  Converting {filename} to PNG, JPG, WEBP...")
        
        try:
            # Use new convert API with auto engine
            convert(str(src_path), str(png_path), engine="auto")
            convert(str(src_path), str(jpg_path), engine="auto", background=(255, 255, 255, 255))
            convert(str(src_path), str(webp_path), engine="auto")
        except Exception as e:
            print(f"  ERROR converting {filename}: {e}")

def convert_with_explicit_engines():
    """Test both engines explicitly for comparison."""
    print("\nTesting explicit engine selection...")
    svg_files = list(OUTPUT_DIR.glob("*.svg"))
    
    from imgshift import convert
    
    # Test with explicit resvg
    print("  Testing with engine='resvg'...")
    test_svg = svg_files[0] if svg_files else None
    if test_svg:
        try:
            out_path = OUTPUT_DIR / f"{test_svg.stem}_engine_resvg.png"
            convert(str(test_svg), str(out_path), engine="resvg")
            print(f"    ✓ Resvg engine worked: {out_path.name}")
        except Exception as e:
            print(f"    ✗ Resvg engine failed: {e}")
    
    # Test with explicit python
    print("  Testing with engine='python'...")
    if test_svg:
        try:
            out_path = OUTPUT_DIR / f"{test_svg.stem}_engine_python.png"
            convert(str(test_svg), str(out_path), engine="python")
            print(f"    ✓ Python engine worked: {out_path.name}")
        except Exception as e:
            print(f"    ✗ Python engine failed: {e}")

def create_html_report():
    """Generate an HTML report comparing original SVG with conversions."""
    print("Generating HTML report...")
    
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>SVG Conversion Report</title>
    <style>
        body { font-family: sans-serif; }
        table { border-collapse: collapse; width: 100%; table-layout: fixed;}
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; vertical-align: middle; word-wrap: break-word; }
        th { background-color: #f2f2f2; }
        img { max-width: 150px; max-height: 150px; border: 1px solid #ccc; background-image: linear-gradient(45deg, #ccc 25%, transparent 25%), linear-gradient(-45deg, #ccc 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #ccc 75%), linear-gradient(-45deg, transparent 75%, #ccc 75%); background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0px; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>SVG Conversion Report</h1>
    <table>
        <thead>
            <tr>
                <th style="width: 15%">Filename</th>
                <th>Original SVG</th>
                <th>Auto (PNG)</th>
                <th>Auto (JPG)</th>
                <th>Auto (WEBP)</th>
                <th>Resvg Engine</th>
                <th>Python Engine</th>
            </tr>
        </thead>
        <tbody>
"""
    svg_files = sorted(list(OUTPUT_DIR.glob("*.svg")))

    for src_path in svg_files:
        filename = src_path.name
        base_name = src_path.stem
        png_file = f"{base_name}.png"
        jpg_file = f"{base_name}.jpg"
        webp_file = f"{base_name}.webp"
        resvg_file = f"{base_name}_engine_resvg.png"
        python_file = f"{base_name}_engine_python.png"
        
        # Check if engine-specific files exist
        resvg_img = f'<img src="{resvg_file}" alt="Resvg">' if (OUTPUT_DIR / resvg_file).exists() else "N/A"
        python_img = f'<img src="{python_file}" alt="Python">' if (OUTPUT_DIR / python_file).exists() else "N/A"
        
        html_content += f"""
            <tr>
                <td>{filename}</td>
                <td><img src="{filename}" alt="Original SVG"></td>
                <td><img src="{png_file}" alt="PNG"></td>
                <td><img src="{jpg_file}" alt="JPG"></td>
                <td><img src="{webp_file}" alt="WEBP"></td>
                <td>{resvg_img}</td>
                <td>{python_img}</td>
            </tr>
"""

    html_content += """
        </tbody>
    </table>
</body>
</html>
"""

    report_path = OUTPUT_DIR / "report.html"
    with open(report_path, "w") as f:
        f.write(html_content)
    
    print(f"Report generated at: {report_path.absolute()}")
    print("Open this file in your browser to inspect the results.")

if __name__ == "__main__":
    create_local_svgs()
    download_external_svgs()
    convert_svgs()
    convert_with_explicit_engines()
    create_html_report()

