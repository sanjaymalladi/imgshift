"""
Quick test to verify winding direction calculation
"""
from imgshift.svg.path_parser import calculate_winding_direction, parse_path, path_to_points

# Test 1: Simple clockwise square
square_cw = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
direction = calculate_winding_direction(square_cw)
print(f"Clockwise square: {direction} (expected: +1)")

# Test 2: Counterclockwise square
square_ccw = [(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)]
direction = calculate_winding_direction(square_ccw)
print(f"Counterclockwise square: {direction} (expected: -1)")

# Test 3: Path with hole (donut)
d = "M 10,10 h80 v80 h-80 z M 30,30 v40 h40 v-40 z"
commands = parse_path(d)
subpaths = path_to_points(commands)

print(f"\nDonut path has {len(subpaths)} subpaths:")
for i, (poly, dir) in enumerate(subpaths):
    print(f"  Subpath {i}: {len(poly)} points, direction={dir}")
    
# Test 4: Simple rectangle path
d2 = "M 10 10 H 90 V 90 H 10 Z"
commands2 = parse_path(d2)
subpaths2 = path_to_points(commands2)
print(f"\nSimple rectangle has {len(subpaths2)} subpaths:")
for i, (poly, dir) in enumerate(subpaths2):
    print(f"  Subpath {i}: {len(poly)} points, direction={dir}")
