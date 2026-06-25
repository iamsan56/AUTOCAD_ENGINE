"""
designs/rectified_hex_spiral.py — Rectified Hexagonal Spiral Microheater

Hexagonal double-pass serpentine spiral with positive full-wave rectifier texture.
Enforces perfect radial phase-locking and straight wavy transitions (no big semicircle heads).
"""

from __future__ import annotations
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.shapes import append_segment, rectified_wave_pts
from config import RECTIFIED_HEX_SPIRAL_PARAMS


def hex_pt(R: float, idx: int) -> tuple[float, float]:
    """
    Vertex of a flat-top regular hexagon.
    idx 0-5: 0=right (0°), going CCW by 60° increments.
    """
    angle = math.radians(60 * idx)
    return (R * math.cos(angle), R * math.sin(angle))


def wavy_hex_path(
    R: float, 
    indices: list[int], 
    amp: float, 
    per: float, 
    outward: bool, 
    N_full: int
) -> list[float]:
    """Generate a sequence of wavy lines passing through the given hexagon vertices."""
    pts: list[float] = []
    for i in range(len(indices) - 1):
        idx0 = indices[i]
        idx1 = indices[i+1]
        x0, y0 = hex_pt(R, idx0)
        x1, y1 = hex_pt(R, idx1)
        
        wave = rectified_wave_pts(x0, y0, x1, y1, amp, per, n_points=max(50, N_full*30), outward=outward, num_bumps=N_full)
        append_segment(pts, wave)
    return pts


def build_path(params: dict | None = None) -> list[float]:
    """Build the complete wavy hexagonal spiral."""
    p           = params or RECTIFIED_HEX_SPIRAL_PARAMS
    R_max       = p["R_max"]
    N           = p["n_rings"]
    track_sep   = p["track_separation"]
    ring_gap    = p["ring_gap"]
    lead_len    = p.get("lead_length", 50.0)
    amp         = p["amplitude"]
    per         = p["period"]
    outward_cfg = p["outward_bumps"]

    # Global bump count based on outermost radius ensures perfect radial phase lock
    N_full = max(1, round(R_max / per))
    band_pitch = track_sep + ring_gap

    # For CW path around hexagon, outward=False makes bumps point outward.
    cw_outward = not outward_cfg
    # For CCW path, outward=True makes bumps point outward.
    ccw_outward = outward_cfg

    all_pts: list[float] = []

    # ── IN terminal lead ──────────────────────────────────────────
    start = hex_pt(R_max, 4)
    lead_angle = math.radians(240)
    lead_tip = (
        start[0] + lead_len * math.cos(lead_angle),
        start[1] + lead_len * math.sin(lead_angle),
    )
    # Wavy lead going inwards to the start vertex
    lead_wave = rectified_wave_pts(lead_tip[0], lead_tip[1], start[0], start[1], amp, per, outward=outward_cfg)
    all_pts.extend(lead_wave)

    # ── Ring bands ────────────────────────────────────────────────
    for i in range(N):
        R_out = R_max - i * band_pitch
        R_in  = R_out - track_sep

        # --- Outer pass (CW): V4 → V3 → V2 → V1 → V0 → V5 ------
        outer_wave = wavy_hex_path(R_out, [4, 3, 2, 1, 0, 5], amp, per, cw_outward, N_full)
        append_segment(all_pts, outer_wave)

        # --- U-turn at V5: outer → inner --------------------------
        # Replaces the smooth bezier curve with a sharp wavy line (no semicircle heads)
        A = hex_pt(R_out, 5)
        B = hex_pt(R_in,  5)
        uturn1 = rectified_wave_pts(A[0], A[1], B[0], B[1], amp, per, outward=outward_cfg)
        append_segment(all_pts, uturn1)

        # --- Inner pass (CCW): V5 → V0 → V1 → V2 → V3 → V4 -----
        inner_wave = wavy_hex_path(R_in, [5, 0, 1, 2, 3, 4], amp, per, ccw_outward, N_full)
        append_segment(all_pts, inner_wave)

        # --- Transition to next ring at V4 ------------------------
        if i < N - 1:
            R_out_next = R_max - (i + 1) * band_pitch
            A = hex_pt(R_in,      4)
            B = hex_pt(R_out_next, 4)
            uturn2 = rectified_wave_pts(A[0], A[1], B[0], B[1], amp, per, outward=outward_cfg)
            append_segment(all_pts, uturn2)

    # ── OUT terminal lead ─────────────────────────────────────────
    R_in_last = R_max - (N - 1) * band_pitch - track_sep
    end_pt = hex_pt(R_in_last, 4)
    lead_tip_out = (
        end_pt[0] + lead_len * math.cos(lead_angle),
        end_pt[1] + lead_len * math.sin(lead_angle),
    )
    # Wavy lead going outwards from the final vertex
    lead_wave_out = rectified_wave_pts(end_pt[0], end_pt[1], lead_tip_out[0], lead_tip_out[1], amp, per, outward=outward_cfg)
    append_segment(all_pts, lead_wave_out)

    return all_pts


DESIGN_META = {
    "name":   "rectified_hex_spiral",
    "title":  "Rectified Hexagonal Spiral",
    "layer":  "MICROHEATER",
    "units":  "micrometers",
    "description": (
        "Double-pass hexagonal spiral with perfect positive full-wave rectifier "
        "semicircles and complete radial phase alignment."
    ),
}

if __name__ == "__main__":
    pts    = build_path()
    n      = len(pts) // 2
    xs, ys = pts[0::2], pts[1::2]
    print(f"Total vertices : {n}")
    print("Successfully generated wavy spiral path.")
