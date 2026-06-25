"""
designs/rectified_hex_spiral.py — Rectified Hexagonal Spiral Microheater

Bifilar (double) continuous hexagonal spiral with positive full-wave rectifier texture.
Features evenly spaced semicircles and a smooth, natural U-turn at the center 
to prevent sharp edges and overlapping.
"""

from __future__ import annotations
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.shapes import append_segment, rectified_wave_pts
from config import RECTIFIED_HEX_SPIRAL_PARAMS


def radial_uturn(A: tuple[float, float], B: tuple[float, float], bulge: float, n: int = 30) -> list[float]:
    """Generates a smooth quadratic Bezier U-turn bridging two points."""
    mx = (A[0] + B[0]) / 2.0
    my = (A[1] + B[1]) / 2.0
    dist = math.hypot(mx, my)
    if dist > 1e-9:
        nx, ny = mx / dist, my / dist
    else:
        nx, ny = 0.0, -1.0
    cx = mx + bulge * nx
    cy = my + bulge * ny
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1.0 - t
        x = mt * mt * A[0] + 2.0 * mt * t * cx + t * t * B[0]
        y = mt * mt * A[1] + 2.0 * mt * t * cy + t * t * B[1]
        pts.extend([x, y])
    return pts


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

    all_pts: list[float] = []
    N_verts = 6 * n_turns
    waypoints = []
    
    # ── Spiral 1 (IN) ──────────────────────────────────────────────
    for i in range(N_verts + 1):
        R = R_max - i * (spacing / 3.0)
        angle = math.radians(240 - i * 60)
        waypoints.append((R * math.cos(angle), R * math.sin(angle)))
        
    # ── Spiral 2 (OUT) ─────────────────────────────────────────────
    for i in range(N_verts, -1, -1):
        R = R_max - spacing - i * (spacing / 3.0)
        angle = math.radians(240 - i * 60)
        waypoints.append((R * math.cos(angle), R * math.sin(angle)))
        
    # ── Leads ──────────────────────────────────────────────────────
    start_angle = math.radians(240)
    
    # IN Lead
    in_start_x = waypoints[0][0] + lead_len * math.cos(start_angle)
    in_start_y = waypoints[0][1] + lead_len * math.sin(start_angle)
    wave_in_lead = rectified_wave_pts(in_start_x, in_start_y, waypoints[0][0], waypoints[0][1], amp, per, outward=outward_cfg)
    all_pts.extend(wave_in_lead)

    # ── Spiral Body ────────────────────────────────────────────────
    for i in range(len(waypoints) - 1):
        x0, y0 = waypoints[i]
        x1, y1 = waypoints[i+1]
        
        if i == N_verts:
            # Smooth, natural U-turn at the center to prevent sharp overlapping edges
            # Negative bulge pulls the curve radially inwards towards the origin
            uturn = radial_uturn((x0, y0), (x1, y1), bulge=-spacing/1.5)
            append_segment(all_pts, uturn)
            continue
            
        if i < N_verts:
            outward = not outward_cfg  # CW
        else:
            outward = outward_cfg      # CCW
            
        # We let the engine naturally calculate num_bumps based on length.
        # This keeps the semicircles perfectly uniform and evenly spaced everywhere,
        # preventing them from shrinking into needles on the inner tracks.
        wave = rectified_wave_pts(
            x0, y0, 
            x1, y1, 
            amp, per, 
            n_points=100, # High resolution for smooth rendering
            outward=outward
        )
        append_segment(all_pts, wave)

    # OUT Lead
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
        "Bifilar (double) continuous Archimedean hexagonal spiral with "
        "evenly-spaced full-wave rectifier semicircles and a smooth center U-turn."
    ),
}

if __name__ == "__main__":
    pts    = build_path()
    n      = len(pts) // 2
    print(f"Total vertices : {n}")
    print("Successfully generated continuous wavy double spiral path.")
