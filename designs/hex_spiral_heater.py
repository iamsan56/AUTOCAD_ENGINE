"""
designs/hex_spiral_heater.py — Hexagonal Spiral Microheater

Concentric flat-top hexagonal rings connected in a serpentine pattern.
The path spirals from the outermost ring inward, with smooth quadratic
Bezier U-turns at the bottom of each ring transition.

Flat-top hexagon vertex index map (circumradius R):
──────────────────────────────────────────────────
        2 ─────── 1
       /           \\
      3             0    ← right vertex at (R, 0)
       \\           /
        4 ─────── 5
           ↑   ↑
           └───┘  U-turns happen here (bottom area)

Vertex angles: 0=0°, 1=60°, 2=120°, 3=180°, 4=240°, 5=300°

Path Topology
─────────────
  Ring 0 (CW):   vertex 4 → 3 → 2 → 1 → 0 → 5   [lower-left to lower-right]
  U-turn right:  ring-0 vertex-5 ──► ring-1 vertex-5
  Ring 1 (CCW):  vertex 5 → 0 → 1 → 2 → 3 → 4   [lower-right to lower-left]
  U-turn left:   ring-1 vertex-4 ──► ring-2 vertex-4
  Ring 2 (CW):   vertex 4 → 3 → 2 → 1 → 0 → 5
  ⋮
  IN  = lower-left  (vertex 4) of ring 0 (outermost)
  OUT = lower-left  (vertex 4) of ring N-1 if N is even
      = lower-right (vertex 5) of ring N-1 if N is odd
"""

from __future__ import annotations
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.shapes import append_segment
from config import HEX_SPIRAL_PARAMS


# ─────────────────────────────────────────────────────────────────
# Hexagon geometry helpers
# ─────────────────────────────────────────────────────────────────

def hex_pt(R: float, idx: int) -> tuple[float, float]:
    """
    Return (x, y) for vertex *idx* of a flat-top hexagon with circumradius R.
    idx 0-5, starting from the right vertex going counterclockwise.
    """
    angle = math.radians(60 * idx)
    return (R * math.cos(angle), R * math.sin(angle))


def ring_cw(R: float) -> list[float]:
    """
    5-side clockwise traversal: lower-left(4) → left(3) → upper-left(2)
                                 → upper-right(1) → right(0) → lower-right(5)
    Returns flat [x,y, x,y, ...] list (6 vertices = 5 sides).
    """
    pts: list[float] = []
    for idx in [4, 3, 2, 1, 0, 5]:
        x, y = hex_pt(R, idx)
        pts.extend([x, y])
    return pts


def ring_ccw(R: float) -> list[float]:
    """
    5-side counter-clockwise traversal: lower-right(5) → right(0) → upper-right(1)
                                         → upper-left(2) → left(3) → lower-left(4)
    Returns flat [x,y, x,y, ...] list (6 vertices = 5 sides).
    """
    pts: list[float] = []
    for idx in [5, 0, 1, 2, 3, 4]:
        x, y = hex_pt(R, idx)
        pts.extend([x, y])
    return pts


def bezier_uturn(
    A: tuple[float, float],
    B: tuple[float, float],
    dip: float,
    n: int = 32,
) -> list[float]:
    """
    Quadratic Bezier curve from A to B that dips *dip* µm below the lower
    of the two endpoints. Used for the bottom U-turn connections.

    Control point is at:
        (midpoint_x,  min(A.y, B.y) - dip)

    Returns flat [x,y, ...] list with n+1 points.
    """
    cx = (A[0] + B[0]) / 2.0
    cy = min(A[1], B[1]) - dip
    pts: list[float] = []
    for i in range(n + 1):
        t = i / n
        mt = 1.0 - t
        x = mt * mt * A[0] + 2.0 * mt * t * cx + t * t * B[0]
        y = mt * mt * A[1] + 2.0 * mt * t * cy + t * t * B[1]
        pts.extend([x, y])
    return pts


# ─────────────────────────────────────────────────────────────────
# Main path builder
# ─────────────────────────────────────────────────────────────────

def build_path(params: dict | None = None) -> list[float]:
    """
    Build the complete hexagonal spiral path as a flat [x,y,...] list.

    Parameters
    ----------
    params : override dict (default: HEX_SPIRAL_PARAMS from config)
    """
    p     = params or HEX_SPIRAL_PARAMS
    R_max = p["R_max"]
    N     = p["n_rings"]
    d     = p["ring_spacing"]
    dip   = p["uturn_dip"]

    # Compute circumradii from outermost to innermost
    rings: list[float] = [R_max - i * d for i in range(N)]

    all_pts: list[float] = []

    for i, R in enumerate(rings):

        # ── Ring traversal (alternating CW / CCW) ────────────────
        seg = ring_cw(R) if i % 2 == 0 else ring_ccw(R)
        append_segment(all_pts, seg)

        # ── U-turn to next ring ───────────────────────────────────
        if i < N - 1:
            R_next = rings[i + 1]

            if i % 2 == 0:
                # CW ring ends at lower-right vertex (5)
                # → U-turn to lower-right vertex (5) of the next ring
                A = hex_pt(R,      5)
                B = hex_pt(R_next, 5)
            else:
                # CCW ring ends at lower-left vertex (4)
                # → U-turn to lower-left vertex (4) of the next ring
                A = hex_pt(R,      4)
                B = hex_pt(R_next, 4)

            append_segment(all_pts, bezier_uturn(A, B, dip))

    return all_pts


# ─────────────────────────────────────────────────────────────────
# Terminal markers
# ─────────────────────────────────────────────────────────────────

def get_terminal_markers(params: dict | None = None) -> list[dict]:
    """
    Return IN / OUT marker definitions for drawing.
    Each dict: {cx, cy, radius, label, lx, ly}
    """
    p      = params or HEX_SPIRAL_PARAMS
    R_max  = p["R_max"]
    N      = p["n_rings"]
    d      = p["ring_spacing"]
    R_min  = R_max - (N - 1) * d
    r_dot  = p.get("track_width", 3.0)

    # IN: lower-left (vertex 4) of outermost ring
    in_x,  in_y  = hex_pt(R_max, 4)

    # OUT: depends on parity of last ring index
    last = N - 1
    if last % 2 == 1:
        # Last ring is odd (CCW) → ends at lower-left (vertex 4)
        out_x, out_y = hex_pt(R_min, 4)
    else:
        # Last ring is even (CW) → ends at lower-right (vertex 5)
        out_x, out_y = hex_pt(R_min, 5)

    return [
        {
            "cx": in_x,  "cy": in_y,  "radius": r_dot,
            "label": "IN",
            "lx": in_x - 9,  "ly": in_y - 6,
        },
        {
            "cx": out_x, "cy": out_y, "radius": r_dot,
            "label": "OUT",
            "lx": out_x + 2, "ly": out_y - 6,
        },
    ]


# ─────────────────────────────────────────────────────────────────
# Design metadata
# ─────────────────────────────────────────────────────────────────

DESIGN_META = {
    "name":         "hex_spiral_heater",
    "title":        "Hexagonal Spiral Microheater",
    "layer":        "MICROHEATER",
    "units":        "micrometers",
    "title_x":      -55.0,   # µm – title text X position (left of geometry)
    "title_y":       55.0,   # µm – title text Y position (above top of hex)
    "title_height":   4.0,
    "description": (
        "Concentric flat-top hexagonal rings in serpentine spiral pattern. "
        "6 rings, 50 µm outer radius, 7 µm ring spacing. "
        "Smooth Bezier U-turns at the bottom of each ring transition."
    ),
}


# ─────────────────────────────────────────────────────────────────
# Self-test: run directly to validate geometry (no AutoCAD needed)
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pts = build_path()
    n_verts = len(pts) // 2
    xs = pts[0::2]
    ys = pts[1::2]

    markers = get_terminal_markers()
    in_m   = markers[0]
    out_m  = markers[1]

    print(f"Total vertices : {n_verts}")
    print(f"X range        : {min(xs):.2f}  …  {max(xs):.2f}  µm")
    print(f"Y range        : {min(ys):.2f}  …  {max(ys):.2f}  µm")
    print(f"IN  terminal   : ({in_m['cx']:.2f}, {in_m['cy']:.2f})")
    print(f"OUT terminal   : ({out_m['cx']:.2f}, {out_m['cy']:.2f})")
    print()

    # Print each ring's start and end for manual verification
    from config import HEX_SPIRAL_PARAMS as P
    rings = [P["R_max"] - i * P["ring_spacing"] for i in range(P["n_rings"])]
    for i, R in enumerate(rings):
        direction = "CW " if i % 2 == 0 else "CCW"
        start_v = 4 if i % 2 == 0 else 5
        end_v   = 5 if i % 2 == 0 else 4
        sv = hex_pt(R, start_v)
        ev = hex_pt(R, end_v)
        print(f"  Ring {i} R={R:5.1f} µm  {direction}  "
              f"start=({sv[0]:6.2f},{sv[1]:6.2f})  end=({ev[0]:6.2f},{ev[1]:6.2f})")
