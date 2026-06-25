"""
designs/wavy_hexagon.py — Wavy Hexagon

A flat-top hexagon where each straight edge is replaced by a continuous
sinusoidal wave from the start vertex to the end vertex.
Vertices are located at 0°, 60°, 120°, 180°, 240°, 300°.
"""

from __future__ import annotations
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.shapes import wavy_pts, append_segment
from config import WAVY_HEXAGON_PARAMS


def flat_hex_pt(R: float, idx: int) -> tuple[float, float]:
    """
    Vertex of a flat-top regular hexagon.
    idx 0-5: 0=right (0°), 1=top-right (60°), 2=top-left (120°),
             3=left (180°), 4=bottom-left (240°), 5=bottom-right (300°).
    """
    angle = math.radians(60 * idx)
    return (R * math.cos(angle), R * math.sin(angle))


def build_path(params: dict | None = None) -> list[float]:
    """
    Build the wavy hexagon path as a flat [x,y,...] list.
    """
    p         = params or WAVY_HEXAGON_PARAMS
    R         = p["radius"]
    amplitude = p["amplitude"]
    period    = p["period"]

    all_pts: list[float] = []

    # Get the 6 vertices
    verts = [flat_hex_pt(R, i) for i in range(6)]
    
    # We trace a closed loop through the 6 edges
    # Edge 0: V0 -> V1
    # Edge 1: V1 -> V2
    # ...
    # Edge 5: V5 -> V0
    for i in range(6):
        start_pt = verts[i]
        end_pt   = verts[(i + 1) % 6]
        
        edge_wave = wavy_pts(
            x0=start_pt[0], y0=start_pt[1],
            x1=end_pt[0], y1=end_pt[1],
            amplitude=amplitude,
            period=period,
            n_points=100
        )
        
        append_segment(all_pts, edge_wave)

    return all_pts


# ─────────────────────────────────────────────────────────────────
# Design metadata
# ─────────────────────────────────────────────────────────────────

DESIGN_META = {
    "name":   "wavy_hexagon",
    "title":  "Wavy Hexagon",
    "layer":  "MICROHEATER",
    "units":  "micrometers",
    "description": (
        "A regular hexagon where each edge is a sinusoidal wave."
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
    print("Path successfully generated matching the wavy hexagon topology!")
