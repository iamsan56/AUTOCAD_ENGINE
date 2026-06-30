"""
designs/large_hex_spiral.py — Large Straight Double Hexagonal Spiral

Bifilar (double) continuous hexagonal spiral with straight lines.
Includes clean separated terminal leads and a smooth center U-turn to avoid overlap.
"""

from __future__ import annotations
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import LARGE_HEX_SPIRAL_PARAMS


def radial_uturn(A: tuple[float, float], B: tuple[float, float], bulge: float, n: int = 20) -> list[float]:
    """Quadratic Bezier U-turn bridging A to B."""
    mx = (A[0] + B[0]) / 2.0
    my = (A[1] + B[1]) / 2.0
    dist = math.hypot(mx, my)
    if dist > 1e-9:
        nx, ny = mx / dist, my / dist
    else:
        nx, ny = 0.0, -1.0

    cx = mx + bulge * nx
    cy = my + bulge * ny

    pts: list[float] = []
    for i in range(1, n + 1):  # Start at 1 to avoid duplicating point A
        t  = i / n
        mt = 1.0 - t
        x  = mt * mt * A[0] + 2.0 * mt * t * cx + t * t * B[0]
        y  = mt * mt * A[1] + 2.0 * mt * t * cy + t * t * B[1]
        pts.extend([x, y])
    return pts


def build_path(params: dict | None = None) -> list[float]:
    """Build the complete bifilar straight hexagonal spiral."""
    p           = params or LARGE_HEX_SPIRAL_PARAMS
    R_max       = p["R_max"]
    n_turns     = p["n_turns"]
    spacing     = p["spacing"]
    lead_len    = p["lead_length"]

    all_pts: list[float] = []
    N_verts = 6 * n_turns
    
    start_angle = math.radians(240)
    
    # ── IN Terminal Lead ─────────────────────────────────────────────
    # Spiral 1 starts at radius R_max, angle 240
    # Extending outwards along the same 240 degree angle
    in_pad_x = (R_max + lead_len) * math.cos(start_angle)
    in_pad_y = (R_max + lead_len) * math.sin(start_angle)
    all_pts.extend([in_pad_x, in_pad_y])
    
    start_x = R_max * math.cos(start_angle)
    start_y = R_max * math.sin(start_angle)
    all_pts.extend([start_x, start_y])
    
    # ── Spiral 1 (IN) ──────────────────────────────────────────────
    for i in range(1, N_verts + 1):
        R = R_max - i * (spacing / 3.0)
        angle = math.radians(240 - i * 60)
        all_pts.extend([R * math.cos(angle), R * math.sin(angle)])
        
    # ── Center Connection ──────────────────────────────────────────
    # Smooth U-turn to completely eliminate sharp corners & track overlap
    A_x, A_y = all_pts[-2], all_pts[-1]
    
    B_R = R_max - spacing - N_verts * (spacing / 3.0)
    B_angle = math.radians(240 - N_verts * 60)
    B_x, B_y = B_R * math.cos(B_angle), B_R * math.sin(B_angle)
    
    all_pts.extend(radial_uturn((A_x, A_y), (B_x, B_y), bulge=-spacing/1.5))
        
    # ── Spiral 2 (OUT) ─────────────────────────────────────────────
    for i in range(N_verts, -1, -1):
        # Skip the first point since radial_uturn just placed it
        if i == N_verts:
            continue
            
        R = R_max - spacing - i * (spacing / 3.0)
        angle = math.radians(240 - i * 60)
        all_pts.extend([R * math.cos(angle), R * math.sin(angle)])
        
    # ── OUT Terminal Lead ────────────────────────────────────────────
    # Spiral 2 ends at R_max - spacing, angle 240
    # Route this lead DOWN-RIGHT (300 degrees) so it does NOT overlap Spiral 1's lead
    out_end_x = (R_max - spacing) * math.cos(start_angle)
    out_end_y = (R_max - spacing) * math.sin(start_angle)
    
    route_angle = math.radians(300)
    out_pad_x = out_end_x + lead_len * math.cos(route_angle)
    out_pad_y = out_end_y + lead_len * math.sin(route_angle)
    
    all_pts.extend([out_pad_x, out_pad_y])

    return all_pts


DESIGN_META = {
    "name":   "large_hex_spiral",
    "title":  "Large Straight Double Hexagonal Spiral",
    "layer":  "MICROHEATER",
    "units":  "micrometers",
    "description": (
        "Large straight-line bifilar hexagonal spiral. "
        "Continuous electrical path with separated leads and smooth center."
    ),
}

if __name__ == "__main__":
    pts    = build_path()
    n      = len(pts) // 2
    print(f"Total vertices : {n}")
    print("Successfully generated continuous straight double spiral path.")