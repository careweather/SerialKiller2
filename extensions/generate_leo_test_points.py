#!/usr/bin/env python3
"""
Generate sphere points representing typical LEO magnetic field vectors at 500km altitude.

Earth's magnetic field at LEO (~500km):
- Equatorial regions: ~250-350 mG, mostly horizontal (along orbit track or perpendicular)
- Mid-latitudes: ~400-500 mG, inclined ~45-60°
- Polar regions: ~550-650 mG, mostly vertical

This script generates test points that:
1. Cover all directions the satellite might see
2. Use realistic magnitudes based on "latitude" (Z-component)
3. Can be used to verify post-calibration residuals
"""

import numpy as np
import os

def generate_leo_sphere_points(num_points=200, output_file="leo_sphere_points.txt"):
    """
    Generate sphere points with LEO-realistic magnitudes.
    
    The magnitude varies based on the Z-component to simulate latitude dependence:
    - High |Z| (polar-like): higher magnitude (~550-600 mG)
    - Low |Z| (equatorial-like): lower magnitude (~300-350 mG)
    """
    
    # Generate evenly distributed points on unit sphere using Fibonacci spiral
    indices = np.arange(0, num_points, dtype=float) + 0.5
    phi = np.arccos(1 - 2 * indices / num_points)  # polar angle
    theta = np.pi * (1 + 5**0.5) * indices  # azimuthal angle (golden ratio)
    
    # Unit sphere coordinates
    x = np.sin(phi) * np.cos(theta)
    y = np.sin(phi) * np.sin(theta)
    z = np.cos(phi)
    
    # Magnitude varies with |z| (latitude proxy)
    # |z| = 0 (equator): ~300 mG
    # |z| = 1 (poles): ~600 mG
    min_mag = 300  # mG at equator
    max_mag = 600  # mG at poles
    magnitudes = min_mag + (max_mag - min_mag) * np.abs(z)
    
    # Scale to actual field vectors
    bx = (x * magnitudes).astype(int)
    by = (y * magnitudes).astype(int)
    bz = (z * magnitudes).astype(int)
    
    # Write to file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_file)
    
    with open(output_path, 'w') as f:
        for i in range(num_points):
            f.write(f"{bx[i]},{by[i]},{bz[i]}\n")
    
    print(f"Generated {num_points} LEO test points to: {output_path}")
    print(f"Magnitude range: {np.min(magnitudes):.0f} to {np.max(magnitudes):.0f} mG")
    
    # Print statistics
    print("\nSample points:")
    print("  Direction          | Magnitude | Vector")
    print("  " + "-" * 50)
    samples = [0, num_points//4, num_points//2, 3*num_points//4, num_points-1]
    for i in samples:
        mag = np.sqrt(bx[i]**2 + by[i]**2 + bz[i]**2)
        desc = "Polar" if abs(z[i]) > 0.8 else "Mid-lat" if abs(z[i]) > 0.4 else "Equator"
        print(f"  {desc:<17} | {mag:>6.0f} mG | ({bx[i]:>4}, {by[i]:>4}, {bz[i]:>4})")
    
    return output_path


def generate_specific_test_vectors(output_file="leo_specific_tests.txt"):
    """
    Generate specific test vectors for key orbital positions.
    These are high-priority vectors to check for residuals.
    """
    
    # Define specific test cases: (description, direction, magnitude_mG)
    test_cases = [
        # Equatorial region (low magnitude, horizontal field)
        ("Equator +X", (1, 0, 0), 300),
        ("Equator -X", (-1, 0, 0), 300),
        ("Equator +Y", (0, 1, 0), 300),
        ("Equator -Y", (0, -1, 0), 300),
        ("Equator XY diagonal", (0.707, 0.707, 0), 320),
        
        # Mid-latitude ascending/descending (medium magnitude, inclined)
        ("Mid-lat asc +X+Z", (0.707, 0, 0.707), 450),
        ("Mid-lat asc -X+Z", (-0.707, 0, 0.707), 450),
        ("Mid-lat desc +X-Z", (0.707, 0, -0.707), 450),
        ("Mid-lat desc -X-Z", (-0.707, 0, -0.707), 450),
        ("Mid-lat +Y+Z", (0, 0.707, 0.707), 450),
        ("Mid-lat +Y-Z", (0, 0.707, -0.707), 450),
        
        # Polar regions (high magnitude, mostly vertical)
        ("Polar +Z", (0, 0, 1), 580),
        ("Polar -Z", (0, 0, -1), 580),
        ("Near-polar +X+Z", (0.3, 0, 0.954), 560),
        ("Near-polar -X+Z", (-0.3, 0, 0.954), 560),
        ("Near-polar +X-Z", (0.3, 0, -0.954), 560),
        
        # 45° all-axis (common transitional state)
        ("45° all axes +++", (0.577, 0.577, 0.577), 480),
        ("45° all axes ++-", (0.577, 0.577, -0.577), 480),
        ("45° all axes +-+", (0.577, -0.577, 0.577), 480),
        ("45° all axes +--", (0.577, -0.577, -0.577), 480),
        
        # South Atlantic Anomaly region (slightly weaker field, specific direction)
        ("SAA region", (0.5, 0.5, 0.707), 350),
    ]
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_file)
    
    with open(output_path, 'w') as f:
        for desc, direction, magnitude in test_cases:
            # Normalize direction and scale
            d = np.array(direction)
            d = d / np.linalg.norm(d)
            bx, by, bz = (d * magnitude).astype(int)
            f.write(f"{bx},{by},{bz}\n")
    
    print(f"\nGenerated {len(test_cases)} specific test vectors to: {output_path}")
    print("\nTest cases:")
    for i, (desc, direction, magnitude) in enumerate(test_cases):
        d = np.array(direction)
        d = d / np.linalg.norm(d)
        bx, by, bz = (d * magnitude).astype(int)
        print(f"  {i+1:2}. {desc:<25} ({bx:>4}, {by:>4}, {bz:>4})")
    
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate LEO test points for magnetometer residual testing")
    parser.add_argument("-n", "--num-points", type=int, default=200, 
                        help="Number of sphere points to generate (default: 200)")
    parser.add_argument("-o", "--output", type=str, default="leo_sphere_points.txt",
                        help="Output filename (default: leo_sphere_points.txt)")
    parser.add_argument("--specific", action="store_true",
                        help="Also generate specific test vectors file")
    parser.add_argument("--specific-only", action="store_true",
                        help="Only generate specific test vectors (fewer points, key directions)")
    
    args = parser.parse_args()
    
    if args.specific_only:
        generate_specific_test_vectors()
    else:
        generate_leo_sphere_points(args.num_points, args.output)
        if args.specific:
            generate_specific_test_vectors()
