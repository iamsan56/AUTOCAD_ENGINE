"""
designs/rectified_hex_spiral.py — Rectified Hexagonal Spiral Microheater

Single-pass continuous hexagonal spiral with positive full-wave rectifier texture.
Enforces perfect radial phase-locking (no crest mismatch) and continuous paths
without any U-turn jumps (no semicircle heads).
"""

from __future__ import annotations
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.shapes import append_segment, rectified_wave_pts
from config import RECTIFIED_HEX_SPIRAL_PARAMS


def build_path(params: dict | None = None) -> list[float]:
    """Build the complete single-pass wavy hexagonal spiral."""
    p           = params or RECTIFIED_HEX_SPIRAL_PARAMS
    R_max       = p["R_max"]
    n_turns     = p["n_turns"]
    spacing     = p["spacing"]
    lead_len    = p.get("lead_length", 50.0)
    amp         = p["amplitude"]
    per         = p["period"]
    outward_cfg = p["outward_bumps"]

    # Global bump count based on outermost radius ensures perfect radial phase lock.
    # Every single straight edge of the spiral will be forced to have exactly this
    # many bumps, regardless of its length. This means the angular spacing of the
    # bumps is identical for all turns, guaranteeing that crests align with crests
    # exactly along the radial axes.
    N_full = max(1, round(R_max / per))

    # The spiral starts at the bottom-left and goes inwards clockwise.
    # For a CW path, the "left" normal vector points away from the center.
    # Since outward_cfg=True means "bulge away from center", we set cw_outward 
    # to the opposite of outward_cfg so the math points in the correct direction.
    cw_outward = not outward_cfg

    all_pts: list[float] = []

    # Calculate vertices of the continuous spiral
    N_verts = 6 * n_turns + 1
    start_angle = 240.0
    
    # ── Terminal Lead ──────────────────────────────────────────────
    lead_angle = math.radians(start_angle)
    start_x = R_max * math.cos(lead_angle)
    start_y = R_max * math.sin(lead_angle)
    
    lead_tip_x = start_x + lead_len * math.cos(lead_angle)
    lead_tip_y = start_y + lead_len * math.sin(lead_angle)
    
    # Wavy lead going inwards to the start vertex
    lead_wave = rectified_wave_pts(lead_tip_x, lead_tip_y, start_x, start_y, amp, per, outward=outward_cfg)
    all_pts.extend(lead_wave)

    # ── Spiral Body ────────────────────────────────────────────────
    waypoints = []
    for i in range(N_verts):
        # Radius decreases continuously at each vertex (Archimedean spiral)
        R = R_max - i * (spacing / 6.0)
        # Angle goes clockwise by 60 degrees per vertex
        angle = math.radians(start_angle - i * 60)
        x = R * math.cos(angle)
        y = R * math.sin(angle)
        waypoints.append((x, y))

    for i in range(len(waypoints) - 1):
        x0, y0 = waypoints[i]
        x1, y1 = waypoints[i+1]
        
        # We enforce exactly N_full bumps per edge.
        # This completely solves the "crest and trough mismatch" problem.
        wave = rectified_wave_pts(
            x0, y0, 
            x1, y1, 
            amp, per, 
            n_points=max(50, N_full * 30), # Solves the low-resolution aliasing
            outward=cw_outward, 
            num_bumps=N_full
        )
        append_segment(all_pts, wave)

    return all_pts


DESIGN_META = {
    "name":   "rectified_hex_spiral",
    "title":  "Rectified Hexagonal Spiral",
    "layer":  "MICROHEATER",
    "units":  "micrometers",
    "description": (
        "Single-pass continuous Archimedean hexagonal spiral with perfect "
        "positive full-wave rectifier semicircles and complete radial phase alignment."
    ),
}


if __name__ == "__main__":
    pts    = build_path()
    n      = len(pts) // 2
    xs, ys = pts[0::2], pts[1::2]
    print(f"Total vertices : {n}")
    print(f"X range        : {min(xs):.1f}  …  {max(xs):.1f}  µm")
    print(f"Y range        : {min(ys):.1f}  …  {max(ys):.1f}  µm")
    print("Successfully generated continuous wavy spiral path.")
