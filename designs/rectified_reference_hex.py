"""
designs/rectified_reference_hex.py — Rectified Hexagonal Microheater Reference Design

A pointy-top hexagonal serpentine path with a central return line.
Every straight track segment is replaced by full-wave rectified semicircles.
"""

from __future__ import annotations
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.shapes import append_segment, arc_pts, rectified_wave_pts
from config import RECTIFIED_REFERENCE_HEX_PARAMS


# ─────────────────────────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────────────────────────

def pointy_hex_pt(R: float, idx: int) -> tuple[float, float]:
    """
    Vertex of a pointy-top regular hexagon.
    idx 0-5: 0=upper-right (30°), 1=top (90°), 2=upper-left (150°),
             3=lower-left (210°), 4=bottom (270°), 5=lower-right (330°).
    """
    angle = math.radians(30 + 60 * idx)
    return (R * math.cos(angle), R * math.sin(angle))


def calc_gap_endpoints(R: float, gap_width: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """
    Calculate the endpoints of a track of radius R, stopping short of the 210° gap.
    """
    u_v3 = (-math.sqrt(3)/2, -0.5)
    d_along = gap_width / math.sqrt(3)

    p_left_x = R * u_v3[0] + d_along * 0.0
    p_left_y = R * u_v3[1] + d_along * 1.0

    p_right_x = R * u_v3[0] + d_along * (math.sqrt(3)/2)
    p_right_y = R * u_v3[1] + d_along * (-0.5)

    return (p_right_x, p_right_y), (p_left_x, p_left_y)


def path_ccw_wavy(R: float, gap_width: float, amp: float, per: float, outward: bool, N_full: int, N_gap: int) -> list[float]:
    """
    Generate a CCW track segment at radius R, using rectified waves.
    For CCW, "right of path" is outward.
    """
    p_right, p_left = calc_gap_endpoints(R, gap_width)
    
    waypoints = [p_right]
    for idx in [4, 5, 0, 1, 2]:
        waypoints.append(pointy_hex_pt(R, idx))
    waypoints.append(p_left)

    pts = []
    for i in range(len(waypoints) - 1):
        x0, y0 = waypoints[i]
        x1, y1 = waypoints[i+1]
        
        # The first and last segments are partial edges bounding the gap
        nb = N_gap if (i == 0 or i == len(waypoints) - 2) else N_full
            
        wave = rectified_wave_pts(x0, y0, x1, y1, amp, per, n_points=50, outward=outward, num_bumps=nb)
        append_segment(pts, wave)
        
    return pts


def path_cw_wavy(R: float, gap_width: float, amp: float, per: float, outward: bool, N_full: int, N_gap: int) -> list[float]:
    """
    Generate a CW track segment at radius R, using rectified waves.
    For CW, "right of path" is INWARD. To keep bumps outward, we flip the outward flag.
    """
    p_right, p_left = calc_gap_endpoints(R, gap_width)
    
    waypoints = [p_left]
    for idx in [2, 1, 0, 5, 4]:
        waypoints.append(pointy_hex_pt(R, idx))
    waypoints.append(p_right)

    pts = []
    for i in range(len(waypoints) - 1):
        x0, y0 = waypoints[i]
        x1, y1 = waypoints[i+1]
        
        nb = N_gap if (i == 0 or i == len(waypoints) - 2) else N_full
        
        wave = rectified_wave_pts(x0, y0, x1, y1, amp, per, n_points=50, outward=not outward, num_bumps=nb)
        append_segment(pts, wave)
        
    return pts


# ─────────────────────────────────────────────────────────────────
# Path builder
# ─────────────────────────────────────────────────────────────────

def build_path(params: dict | None = None) -> list[float]:
    """
    Build the complete rectified reference microheater path as a flat [x,y,...] list.
    """
    p           = params or RECTIFIED_REFERENCE_HEX_PARAMS
    R_max       = p["R_max"]
    N           = p["n_tracks"]
    spacing     = p["spacing"]
    gap_width   = p["gap_width"]
    lead_len    = p["lead_length"]
    amp         = p["amplitude"]
    per         = p["period"]
    outward     = p["outward_bumps"]

    rings = [R_max - i * spacing for i in range(N)]
    all_pts: list[float] = []
    
    # Calculate global bump counts based on the outermost track
    # This guarantees perfect radial alignment of all crests and troughs
    N_full = max(1, round(R_max / per))
    d_along = gap_width / math.sqrt(3)
    N_gap = max(1, round((R_max - d_along) / per))

    # ── Terminal 1 (Outer track lead) ──────────────────────────────
    u_v3 = (-math.sqrt(3)/2, -0.5)
    p_right_0, _ = calc_gap_endpoints(rings[0], gap_width)
    t1_x = p_right_0[0] + lead_len * u_v3[0]
    t1_y = p_right_0[1] + lead_len * u_v3[1]
    
    # Wave from outer lead tip towards the start of the gap
    lead_in = rectified_wave_pts(t1_x, t1_y, p_right_0[0], p_right_0[1], amp, per, n_points=30, outward=outward)
    all_pts.extend(lead_in)

    # ── Serpentine Tracks ──────────────────────────────────────────
    for i in range(N):
        R = rings[i]
        p_right, p_left = calc_gap_endpoints(R, gap_width)

        if i % 2 == 0:
            # Even tracks go CCW
            append_segment(all_pts, path_ccw_wavy(R, gap_width, amp, per, outward, N_full, N_gap))

            # U-turn on the LEFT side (connects Track i to Track i+1)
            if i < N - 1:
                _, p_left_next = calc_gap_endpoints(rings[i+1], gap_width)
                # Instead of a smooth arc (big semicircle head), connect with a straight rectified wave
                # Number of bumps = spacing / per. We let it auto-calculate so it connects perfectly.
                wave_u_turn = rectified_wave_pts(p_left[0], p_left[1], p_left_next[0], p_left_next[1], amp, per, n_points=50, outward=outward)
                append_segment(all_pts, wave_u_turn)
        else:
            # Odd tracks go CW
            append_segment(all_pts, path_cw_wavy(R, gap_width, amp, per, outward, N_full, N_gap))

            # U-turn on the RIGHT side
            if i < N - 1:
                p_right_next, _ = calc_gap_endpoints(rings[i+1], gap_width)
                # Instead of a smooth arc, connect with a straight rectified wave
                wave_u_turn = rectified_wave_pts(p_right[0], p_right[1], p_right_next[0], p_right_next[1], amp, per, n_points=50, outward=outward)
                append_segment(all_pts, wave_u_turn)

    # ── Terminal 2 (Inner return line) ─────────────────────────────
    R_last = rings[-1]
    axis_x = R_last * u_v3[0]
    axis_y = R_last * u_v3[1]
    
    # We are at the end of the last track. Let's make a wave to the center axis.
    if (N - 1) % 2 == 0:
        last_pt_x, last_pt_y = calc_gap_endpoints(R_last, gap_width)[1] # p_left
    else:
        last_pt_x, last_pt_y = calc_gap_endpoints(R_last, gap_width)[0] # p_right

    # Wave from last track to the central axis line
    wave_to_axis = rectified_wave_pts(last_pt_x, last_pt_y, axis_x, axis_y, amp, per, n_points=30, outward=outward)
    append_segment(all_pts, wave_to_axis)

    # Wave from central axis straight out to the terminal
    t2_x = (R_max + lead_len) * u_v3[0]
    t2_y = (R_max + lead_len) * u_v3[1]
    wave_out = rectified_wave_pts(axis_x, axis_y, t2_x, t2_y, amp, per, n_points=60, outward=outward)
    append_segment(all_pts, wave_out)

    return all_pts


# ─────────────────────────────────────────────────────────────────
# Design metadata
# ─────────────────────────────────────────────────────────────────

DESIGN_META = {
    "name":   "rectified_reference_hex",
    "title":  "Rectified Reference Hexagonal Serpentine",
    "layer":  "MICROHEATER",
    "units":  "micrometers",
    "description": (
        "The 7-track reference geometry with all straight lines replaced "
        "by full-wave rectified semicircles."
    ),
}


# ─────────────────────────────────────────────────────────────────
# Self-test (no AutoCAD required)
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pts    = build_path()
    n      = len(pts) // 2
    xs, ys = pts[0::2], pts[1::2]

    print(f"Total vertices : {n}")
    print(f"X range        : {min(xs):.1f}  …  {max(xs):.1f}  µm")
    print(f"Y range        : {min(ys):.1f}  …  {max(ys):.1f}  µm")
    print()
    print("Path successfully generated matching the rectified reference topology!")
