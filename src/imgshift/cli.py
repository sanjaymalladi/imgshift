"""
Command-line interface for imgshift.

Uses stdlib argparse for zero external dependencies.
"""

import argparse
import sys
from pathlib import Path
from typing import List

from imgshift.core import convert
from imgshift.utils import ALL_FORMATS


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='imgshift',
        description='Convert images between formats. Exceptional SVG support.',
        epilog='Examples:\n'
               '  imgshift icon.svg icon.png\n'
               '  imgshift photo.png photo.jpg --quality 90\n'
               '  imgshift document.pdf page.png --page 0 --dpi 300\n'
               '  imgshift *.png --to pdf --output combined.pdf\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'input',
        nargs='+',
        help='Input file(s). Supports glob patterns for batch conversion.'
    )
    
    parser.add_argument(
        'output',
        nargs='?',
        help='Output file path. Required for single file conversion.'
    )
    
    parser.add_argument(
        '-t', '--to',
        metavar='FORMAT',
        help='Target format for batch conversion (e.g., png, jpg, pdf)'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        metavar='DIR',
        help='Output directory for batch conversion'
    )
    
    parser.add_argument(
        '-w', '--width',
        type=int,
        metavar='PX',
        help='Target width in pixels'
    )
    
    parser.add_argument(
        '-H', '--height',
        type=int,
        metavar='PX',
        help='Target height in pixels'
    )
    
    parser.add_argument(
        '-q', '--quality',
        type=int,
        default=85,
        metavar='N',
        help='JPEG quality 1-100 (default: 85)'
    )
    
    parser.add_argument(
        '-d', '--dpi',
        type=int,
        default=150,
        metavar='N',
        help='DPI for PDF/SVG rendering (default: 150)'
    )
    
    parser.add_argument(
        '-p', '--page',
        type=int,
        metavar='N',
        help='PDF page number to convert (0-indexed)'
    )
    
    parser.add_argument(
        '--bg',
        metavar='COLOR',
        default='white',
        help='Background color for SVG (e.g., white, #ff0000, transparent)'
    )
    
    parser.add_argument(
        '--engine',
        choices=['auto', 'resvg', 'python'],
        default='auto',
        help='SVG rendering engine: auto (try resvg, fallback to python), resvg (production), or python (experimental)'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='Show version and exit'
    )
    
    args = parser.parse_args()
    
    if args.version:
        from imgshift import __version__
        print(f'imgshift {__version__}')
        return 0
    
    # Parse background color
    background = _parse_bg_color(args.bg)
    
    # Handle different modes
    try:
        if args.to or args.output_dir:
            # Batch conversion
            _batch_convert(args, background)
        elif len(args.input) > 1 and args.output:
            # Multiple inputs to single output (e.g., images to PDF)
            _multi_to_one(args, background)
        elif len(args.input) == 1 and args.output:
            # Single file conversion
            _single_convert(args, background)
        else:
            parser.error('Please provide input and output files, or use --to/--output-dir for batch conversion')
            return 1
            
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1
    
    return 0


def _parse_bg_color(color_str: str):
    """Parse background color argument."""
    from imgshift.utils import parse_color
    return parse_color(color_str)


def _single_convert(args, background):
    """Convert a single file."""
    input_path = args.input[0]
    output_path = args.output
    
    print(f'Converting {input_path} -> {output_path}')
    
    convert(
        input_path,
        output_path,
        width=args.width,
        height=args.height,
        quality=args.quality,
        dpi=args.dpi,
        page=args.page,
        background=background,
        engine=args.engine
    )
    
    print('Done!')


def _multi_to_one(args, background):
    """Convert multiple inputs to single output (e.g., images to PDF)."""
    print(f'Combining {len(args.input)} files -> {args.output}')
    
    convert(
        args.input,
        args.output,
        quality=args.quality,
        dpi=args.dpi,
        background=background,
        engine=args.engine
    )
    
    print('Done!')


def _batch_convert(args, background):
    """Batch convert files."""
    # Determine target format
    target_ext = args.to
    if target_ext and not target_ext.startswith('.'):
        target_ext = '.' + target_ext
    
    # Determine output directory
    output_dir = Path(args.output_dir) if args.output_dir else Path('.')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each input file
    converted = 0
    for input_pattern in args.input:
        input_path = Path(input_pattern)
        
        # Handle glob patterns
        if '*' in str(input_path):
            files = list(input_path.parent.glob(input_path.name))
        else:
            files = [input_path]
        
        for input_file in files:
            if not input_file.exists():
                print(f'Skipping {input_file} (not found)', file=sys.stderr)
                continue
            
            # Determine output filename
            if target_ext:
                output_file = output_dir / (input_file.stem + target_ext)
            else:
                print(f'Skipping {input_file} (no target format)', file=sys.stderr)
                continue
            
            print(f'Converting {input_file} -> {output_file}')
            
            convert(
                input_file,
                output_file,
                width=args.width,
                height=args.height,
                quality=args.quality,
                dpi=args.dpi,
                page=args.page,
                background=background,
                engine=args.engine
            )
            
            converted += 1
    
    print(f'Converted {converted} file(s)')


def upscale_main():
    """CLI entry point for upscale command."""
    from imgshift.core import upscale
    
    parser = argparse.ArgumentParser(
        prog='imgshift-upscale',
        description='Upscale images using high-quality interpolation (no AI).',
        epilog='Examples:\n'
               '  imgshift-upscale logo.png logo_2x.png --scale 2\n'
               '  imgshift-upscale icon.webp icon_hd.png --width 1024\n'
               '  imgshift-upscale photo.jpg photo_4x.jpg --scale 4 --method bicubic\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'input',
        help='Input image file (PNG, WEBP, JPEG, etc.)'
    )
    
    parser.add_argument(
        'output',
        help='Output image file'
    )
    
    parser.add_argument(
        '-s', '--scale',
        type=float,
        metavar='N',
        help='Scale factor (e.g., 2 for 2x, 4 for 4x)'
    )
    
    parser.add_argument(
        '-w', '--width',
        type=int,
        metavar='PX',
        help='Target width in pixels (maintains aspect ratio if height not specified)'
    )
    
    parser.add_argument(
        '-H', '--height',
        type=int,
        metavar='PX',
        help='Target height in pixels (maintains aspect ratio if width not specified)'
    )
    
    parser.add_argument(
        '-m', '--method',
        default='lanczos',
        choices=['lanczos', 'bicubic', 'bilinear', 'nearest'],
        help='Resampling method (default: lanczos - sharpest for logos)'
    )
    
    parser.add_argument(
        '-q', '--quality',
        type=int,
        default=95,
        metavar='N',
        help='Output quality 1-100 for lossy formats (default: 95)'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='Show version and exit'
    )
    
    args = parser.parse_args()
    
    if args.version:
        from imgshift import __version__
        print(f'imgshift {__version__}')
        return 0
    
    if not args.scale and not args.width and not args.height:
        parser.error('Must specify --scale or --width/--height')
        return 1
    
    try:
        print(f'Upscaling {args.input} -> {args.output}')
        
        upscale(
            args.input,
            args.output,
            scale=args.scale,
            width=args.width,
            height=args.height,
            method=args.method,
            quality=args.quality
        )
        
        print('Done!')
        return 0
        
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

