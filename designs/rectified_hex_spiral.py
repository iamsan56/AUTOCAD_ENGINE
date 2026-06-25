"""
designs/rectified_hex_spiral.py — Rectified Hexagonal Spiral Microheater

Bifilar (double) continuous hexagonal spiral with positive full-wave rectifier texture.
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
    """Build the complete bifilar wavy hexagonal spiral."""
    p           = params or RECTIFIED_HEX_SPIRAL_PARAMS
    R_max       = p["R_max"]
    n_turns     = p["n_turns"]
    spacing     = p["spacing"]
    lead_len    = p.get("lead_length", 50.0)
    amp         = p["amplitude"]
    per         = p["period"]
    outward_cfg = p["outward_bumps"]

    # Global bump count based on outermost radius ensures perfect radial phase lock.
    N_full = max(1, round(R_max / per))

    all_pts: list[float] = []

    N_verts = 6 * n_turns
    waypoints = []
    
    # ── Spiral 1 (IN) ──────────────────────────────────────────────
    # Spirals inwards clockwise
    for i in range(N_verts + 1):
        R = R_max - i * (spacing / 3.0)
        angle = math.radians(240 - i * 60)
        waypoints.append((R * math.cos(angle), R * math.sin(angle)))
        
    # ── Spiral 2 (OUT) ─────────────────────────────────────────────
    # Spirals outwards counter-clockwise (generated backwards from center)
    for i in range(N_verts, -1, -1):
        R = R_max - spacing - i * (spacing / 3.0)
        angle = math.radians(240 - i * 60)
        waypoints.append((R * math.cos(angle), R * math.sin(angle)))
        
    # ── Leads ──────────────────────────────────────────────────────
    start_angle = math.radians(240)
    
    # IN Lead (connects to waypoint 0)
    in_start_x = waypoints[0][0] + lead_len * math.cos(start_angle)
    in_start_y = waypoints[0][1] + lead_len * math.sin(start_angle)
    wave_in_lead = rectified_wave_pts(in_start_x, in_start_y, waypoints[0][0], waypoints[0][1], amp, per, outward=outward_cfg)
    all_pts.extend(wave_in_lead)

    # ── Spiral Body ────────────────────────────────────────────────
    for i in range(len(waypoints) - 1):
        x0, y0 = waypoints[i]
        x1, y1 = waypoints[i+1]
        
        # Spiral 1 (IN) is CW. Spiral 2 (OUT) is CCW.
        if i < N_verts:
            outward = not outward_cfg  # CW
        else:
            outward = outward_cfg      # CCW
            
        wave = rectified_wave_pts(
            x0, y0, 
            x1, y1, 
            amp, per, 
            n_points=max(50, N_full * 30),
            outward=outward, 
            num_bumps=N_full
        )
        append_segment(all_pts, wave)

    # OUT Lead (connects to last waypoint)
    last_pt = waypoints[-1]
    out_end_x = last_pt[0] + lead_len * math.cos(start_angle)
    out_end_y = last_pt[1] + lead_len * math.sin(start_angle)
    wave_out_lead = rectified_wave_pts(last_pt[0], last_pt[1], out_end_x, out_end_y, amp, per, outward=outward_cfg)
    append_segment(all_pts, wave_out_lead)

    return all_pts


DESIGN_META = {
    "name":   "rectified_hex_spiral",
    "title":  "Rectified Hexagonal Spiral",
    "layer":  "MICROHEATER",
    "units":  "micrometers",
    "description": (
        "Bifilar (double) continuous Archimedean hexagonal spiral with perfect "
        "positive full-wave rectifier semicircles and complete radial phase alignment."
    ),
}

if __name__ == "__main__":
    pts    = build_path()
    n      = len(pts) // 2
    print(f"Total vertices : {n}")
    print("Successfully generated continuous wavy double spiral path.")
