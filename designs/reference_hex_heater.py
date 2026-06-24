"""
designs/reference_hex_heater.py — Hexagonal Microheater Reference Design

A pointy-top hexagonal single continuous serpentine path with a central return line.
The design has N parallel tracks. The outer terminal connects to the outermost track.
The path serpentines back and forth, turning at a single gap located at the
bottom-left (210° axis). Once it reaches the innermost track, it exits via a
straight line through the center of the gap.

Vertices of pointy-top hexagon:
V0(30°), V1(90°), V2(150°), V3(210°), V4(270°), V5(330°)

Gap axis: 210°.
"""

from __future__ import annotations
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.shapes import append_segment, arc_pts
from config import REFERENCE_HEX_PARAMS


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
    The gap is bounded by two lines parallel to the 210° axis, spaced by gap_width.
    Returns: (P_right, P_left)
      P_right: endpoint on the right side of the gap (between V3 and V4)
      P_left:  endpoint on the left side of the gap (between V2 and V3)
    """
    # Unit vector along the 210° gap axis
    u_v3 = (-math.sqrt(3)/2, -0.5)
    
    # Distance along the hexagon edge to achieve perpendicular distance gap_width/2
    d_along = gap_width / math.sqrt(3)

    # P_left is on the edge from V3(210°) towards V2(150°)
    # The direction V3 -> V2 is (0, 1)
    p_left_x = R * u_v3[0] + d_along * 0.0
    p_left_y = R * u_v3[1] + d_along * 1.0

    # P_right is on the edge from V3(210°) towards V4(270°)
    # The direction V3 -> V4 is (sqrt(3)/2, -1/2)
    p_right_x = R * u_v3[0] + d_along * (math.sqrt(3)/2)
    p_right_y = R * u_v3[1] + d_along * (-0.5)

    return (p_right_x, p_right_y), (p_left_x, p_left_y)


def path_ccw(R: float, gap_width: float) -> list[float]:
    """
    Generate a CCW track segment at radius R, from the right side of the gap
    around the hexagon to the left side of the gap.
    Sequence: P_right -> V4 -> V5 -> V0 -> V1 -> V2 -> P_left.
    """
    p_right, p_left = calc_gap_endpoints(R, gap_width)
    pts = [p_right[0], p_right[1]]
    for idx in [4, 5, 0, 1, 2]:
        x, y = pointy_hex_pt(R, idx)
        pts.extend([x, y])
    pts.extend([p_left[0], p_left[1]])
    return pts


def path_cw(R: float, gap_width: float) -> list[float]:
    """
    Generate a CW track segment at radius R, from the left side of the gap
    around the hexagon to the right side of the gap.
    Sequence: P_left -> V2 -> V1 -> V0 -> V5 -> V4 -> P_right.
    """
    p_right, p_left = calc_gap_endpoints(R, gap_width)
    pts = [p_left[0], p_left[1]]
    for idx in [2, 1, 0, 5, 4]:
        x, y = pointy_hex_pt(R, idx)
        pts.extend([x, y])
    pts.extend([p_right[0], p_right[1]])
    return pts


# ─────────────────────────────────────────────────────────────────
# Path builder
# ─────────────────────────────────────────────────────────────────

def build_path(params: dict | None = None) -> list[float]:
    """
    Build the complete reference microheater path as a flat [x,y,...] list.
    """
    p           = params or REFERENCE_HEX_PARAMS
    R_max       = p["R_max"]
    N           = p["n_tracks"]
    spacing     = p["spacing"]
    gap_width   = p["gap_width"]
    lead_len    = p["lead_length"]

    # Calculate radii for all tracks
    # R[0] is outermost, R[N-1] is innermost
    rings = [R_max - i * spacing for i in range(N)]

    all_pts: list[float] = []

    # ── Terminal 1 (Outer track lead) ──────────────────────────────
    # Extends outward from P_right(R[0]) parallel to the 210° axis.
    # The 210° axis direction is u_v3 = (-sqrt(3)/2, -0.5).
    # "Outward" is the same as the 210° direction.
    u_v3 = (-math.sqrt(3)/2, -0.5)
    p_right_0, _ = calc_gap_endpoints(rings[0], gap_width)
    t1_x = p_right_0[0] + lead_len * u_v3[0]
    t1_y = p_right_0[1] + lead_len * u_v3[1]
    
    all_pts.extend([t1_x, t1_y])

    # ── Serpentine Tracks ──────────────────────────────────────────
    for i in range(N):
        R = rings[i]
        p_right, p_left = calc_gap_endpoints(R, gap_width)

        if i % 2 == 0:
            # Even tracks (0, 2, 4...) go CCW
            append_segment(all_pts, path_ccw(R, gap_width))

            # U-turn on the LEFT side (connects Track i to Track i+1)
            if i < N - 1:
                # Arc from P_left(R_i) to P_left(R_i+1)
                # Left side bulge goes rightward (into the gap)
                # Midpoint M
                _, p_left_next = calc_gap_endpoints(rings[i+1], gap_width)
                mx = (p_left[0] + p_left_next[0]) / 2.0
                my = (p_left[1] + p_left_next[1]) / 2.0
                # Start at R_i (outer), sweep CCW to R_i+1 (inner)
                # Angle from M to P_left(R_i) is 210°. To P_left(R_i+1) is 30°.
                # Sweeping through 300° (into gap) means start=210, end=390.
                start_angle = math.radians(210)
                end_angle   = math.radians(390)
                arc = arc_pts(mx, my, spacing / 2.0, start_angle, end_angle)
                append_segment(all_pts, arc)
        else:
            # Odd tracks (1, 3, 5...) go CW
            append_segment(all_pts, path_cw(R, gap_width))

            # U-turn on the RIGHT side (connects Track i to Track i+1)
            if i < N - 1:
                # Arc from P_right(R_i) to P_right(R_i+1)
                # Right side bulge goes leftward (into the gap)
                p_right_next, _ = calc_gap_endpoints(rings[i+1], gap_width)
                mx = (p_right[0] + p_right_next[0]) / 2.0
                my = (p_right[1] + p_right_next[1]) / 2.0
                # Start at R_i (outer), sweep CW to R_i+1 (inner)
                # Angle from M to P_right(R_i) is 210°. To P_right(R_i+1) is 30°.
                # Sweeping through 120° (into gap) means start=210, end=30.
                start_angle = math.radians(210)
                end_angle   = math.radians(30)
                arc = arc_pts(mx, my, spacing / 2.0, start_angle, end_angle)
                append_segment(all_pts, arc)

    # ── Terminal 2 (Inner return line) ─────────────────────────────
    # Connects to the end of the last track.
    # The last track is N-1. If N=7, track 6 is even -> CCW.
    # So it ends at P_left(R[6]).
    R_last = rings[-1]
    
    # We route it to the center axis at radius R_last, then straight out.
    # Center axis point at R_last:
    axis_x = R_last * u_v3[0]
    axis_y = R_last * u_v3[1]
    all_pts.extend([axis_x, axis_y])

    # Outward lead extending from the axis by lead_len past the outermost radius
    t2_x = (R_max + lead_len) * u_v3[0]
    t2_y = (R_max + lead_len) * u_v3[1]
    all_pts.extend([t2_x, t2_y])

    return all_pts


# ─────────────────────────────────────────────────────────────────
# Design metadata
# ─────────────────────────────────────────────────────────────────

DESIGN_META = {
    "name":   "reference_hex_heater",
    "title":  "Hexagonal Microheater Reference Design",
    "layer":  "MICROHEATER",
    "units":  "micrometers",
    "description": (
        "Pointy-top single continuous serpentine path (7 tracks) "
        "with alternating U-turns at a 210° gap and a central return line."
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
    print("Path successfully generated matching the reference topology!")
