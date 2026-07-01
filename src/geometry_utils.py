"""
src/geometry_utils.py

Utilities for 2D geometry manipulation, specifically converting 1D mathematical 
centerlines into 2D solid footprints for FEM simulation in COMSOL.
"""

from typing import List

try:
    from shapely.geometry import LineString
except ImportError:
    LineString = None


def offset_polyline(pts: List[float], width: float) -> List[float]:
    """
    Given a flat list of 2D coordinates [x1, y1, x2, y2, ...],
    creates a closed 2D polygon footprint by buffering the line by width/2.
    Returns a flat list of coordinates representing the closed boundary.
    
    cap_style=2 (flat cap)
    join_style=2 (mitre join) -> keeps corners sharp and clean
    """
    if LineString is None:
        raise ImportError("The 'shapely' library is required to generate 2D offsets for COMSOL.")
        
    if len(pts) < 4:
        return []
    
    # Convert flat list to list of tuples
    line_coords = [(pts[i], pts[i+1]) for i in range(0, len(pts), 2)]
    line = LineString(line_coords)
    
    # Buffer to create polygon
    poly = line.buffer(width / 2.0, cap_style=2, join_style=2)
    
    if poly.is_empty:
        return []
        
    exterior_coords = list(poly.exterior.coords)
    
    # Flatten
    flat_poly = []
    for x, y in exterior_coords:
        flat_poly.extend([x, y])
        
    return flat_poly
