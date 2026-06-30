"""
designs/large_hex_spiral.py — Large Straight Double Hexagonal Spiral

Bifilar (double) continuous hexagonal spiral with straight lines.
Includes 1000x1000 um terminal pads.
"""

from __future__ import annotations
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import LARGE_HEX_SPIRAL_PARAMS


def draw_square_pad(cx: float, cy: float, size: float) -> list[float]:
    """Return a closed square polyline centered at (cx, cy)."""
    hs = size / 2.0
    return [
        cx, cy,               # Start at center (to connect from lead)
        cx - hs, cy,          # Go left
        cx - hs, cy - hs,     # Go down
        cx + hs, cy - hs,     # Go right
        cx + hs, cy + hs,     # Go up
        cx - hs, cy + hs,     # Go left
        cx - hs, cy,          # Return to left-center
        cx, cy                # Return to center
    ]


def build_path(params: dict | None = None) -> list[float]:
    """Build the complete bifilar straight hexagonal spiral."""
    p           = params or LARGE_HEX_SPIRAL_PARAMS
    R_max       = p["R_max"]
    n_turns     = p["n_turns"]
    spacing     = p["spacing"]
    pad_size    = p["pad_size"]
    lead_len    = p["lead_length"]

    all_pts: list[float] = []
    N_verts = 6 * n_turns
    
    start_angle = math.radians(240)
    
    # ── IN Terminal Pad ─────────────────────────────────────────────
    # Spiral 1 starts at radius R_max, angle 240
    in_cx = (R_max + lead_len) * math.cos(start_angle)
    in_cy = (R_max + lead_len) * math.sin(start_angle)
    
    # Draw pad 1
    pad1_pts = draw_square_pad(in_cx, in_cy, pad_size)
    all_pts.extend(pad1_pts)
    
    # Connect from pad to spiral start
    start_x = R_max * math.cos(start_angle)
    start_y = R_max * math.sin(start_angle)
    all_pts.extend([start_x, start_y])
    
    # ── Spiral 1 (IN) ──────────────────────────────────────────────
    for i in range(1, N_verts + 1):
        R = R_max - i * (spacing / 3.0)
        angle = math.radians(240 - i * 60)
        all_pts.extend([R * math.cos(angle), R * math.sin(angle)])
        
    # ── Center Connection ──────────────────────────────────────────
    # The straight line connecting Spiral 1 to Spiral 2 is automatically formed
    # by just continuing to the first point of Spiral 2!
        
    # ── Spiral 2 (OUT) ─────────────────────────────────────────────
    for i in range(N_verts, -1, -1):
        R = R_max - spacing - i * (spacing / 3.0)
        angle = math.radians(240 - i * 60)
        all_pts.extend([R * math.cos(angle), R * math.sin(angle)])
        
    # ── OUT Terminal Pad ────────────────────────────────────────────
    # Spiral 2 ends at R_max - spacing, angle 240    
    out_cx = (R_max - spacing + lead_len) * math.cos(start_angle)
    out_cy = (R_max - spacing + lead_len) * math.sin(start_angle)
    
    # Connect from spiral end to pad center
    all_pts.extend([out_cx, out_cy])
    
    # Draw pad 2 (skip the first vertex to avoid duplicating the center point)
    pad2_pts = draw_square_pad(out_cx, out_cy, pad_size)
    all_pts.extend(pad2_pts[2:])

    return all_pts


DESIGN_META = {
    "name":   "large_hex_spiral",
    "title":  "Large Straight Double Hexagonal Spiral",
    "layer":  "MICROHEATER",
    "units":  "micrometers",
    "description": (
        "Large 32x32mm straight-line bifilar hexagonal spiral with 5 turns. "
        "Continuous electrical path with 1000x1000um terminal pads."
    ),
}

if __name__ == "__main__":
    pts    = build_path()
    n      = len(pts) // 2
    print(f"Total vertices : {n}")
    print("Successfully generated continuous straight double spiral path.")
