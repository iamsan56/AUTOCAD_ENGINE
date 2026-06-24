"""
designs/hex_spiral_heater.py — Hexagonal Spiral Microheater

Concentric flat-top hexagonal rings connected in a serpentine pattern.
Each ring shares 5 of its 6 sides with the path; the 6th side (bottom) is
replaced by a smooth quadratic-Bezier U-turn that connects to the next
inner ring.

Flat-top hexagon vertex index (circumradius R)
──────────────────────────────────────────────
         2 ───────── 1
        /             \\
       3               0   ← (R, 0)
        \\             /
         4 ───────── 5
              ↑
         U-turns here

  idx : angle  : coordinates
   0  :   0°   : ( R,        0       )  right
   1  :  60°   : ( R/2,     R·√3/2  )  upper-right
   2  : 120°   : (-R/2,     R·√3/2  )  upper-left
   3  : 180°   : (-R,        0       )  left
   4  : 240°   : (-R/2,    -R·√3/2  )  lower-left
   5  : 300°   : ( R/2,    -R·√3/2  )  lower-right

Path
────
  Ring 0 (CW)   vertex 4→3→2→1→0→5  (lower-left → lower-right)
  U-turn right  ring-0 v5 → ring-1 v5
  Ring 1 (CCW)  vertex 5→0→1→2→3→4  (lower-right → lower-left)
  U-turn left   ring-1 v4 → ring-2 v4
  Ring 2 (CW)   …
  ⋮
  IN  = lower-left vertex of outermost ring
  OUT = lower-left vertex of innermost ring  (when n_rings is even)
        lower-right vertex of innermost ring (when n_rings is odd)
"""

from __future__ import annotations
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.shapes import append_segment
from config import HEX_SPIRAL_PARAMS


# ─────────────────────────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────────────────────────

def hex_pt(R: float, idx: int) -> tuple[float, float]:
    """Return (x, y) of vertex *idx* for a flat-top hexagon with circumradius R."""
    angle = math.radians(60 * idx)
    return (R * math.cos(angle), R * math.sin(angle))


def ring_cw(R: float) -> list[float]:
    """
    Clockwise traversal (5 sides):
    lower-left(4) → left(3) → upper-left(2) → upper-right(1) → right(0) → lower-right(5)
    Returns flat [x,y, x,y, …].
    """
    pts: list[float] = []
    for idx in [4, 3, 2, 1, 0, 5]:
        x, y = hex_pt(R, idx)
        pts.extend([x, y])
    return pts


def ring_ccw(R: float) -> list[float]:
    """
    Counter-clockwise traversal (5 sides):
    lower-right(5) → right(0) → upper-right(1) → upper-left(2) → left(3) → lower-left(4)
    Returns flat [x,y, x,y, …].
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
    n: int = 24,
) -> list[float]:
    """
    Quadratic Bezier U-turn from A to B, curving *dip* µm below the lower point.

    Control point:  ( midpoint_x ,  min(Ay, By) - dip )

    This creates a smooth concave arc that matches the rounded corners
    shown in the hand-drawn sketch.
    """
    cx = (A[0] + B[0]) / 2.0
    cy = min(A[1], B[1]) - dip
    pts: list[float] = []
    for i in range(n + 1):
        t  = i / n
        mt = 1.0 - t
        x  = mt * mt * A[0] + 2.0 * mt * t * cx + t * t * B[0]
        y  = mt * mt * A[1] + 2.0 * mt * t * cy + t * t * B[1]
        pts.extend([x, y])
    return pts


# ─────────────────────────────────────────────────────────────────
# Path builder
# ─────────────────────────────────────────────────────────────────

def build_path(params: dict | None = None) -> list[float]:
    """
    Build the complete hexagonal spiral as a flat [x,y,…] list.

    Segment sequence for N rings:
        Ring-0 CW → U-turn-right → Ring-1 CCW → U-turn-left
        → Ring-2 CW → U-turn-right → … → Ring-(N-1)
    """
    p     = params or HEX_SPIRAL_PARAMS
    R_max = p["R_max"]
    N     = p["n_rings"]
    d     = p["ring_spacing"]
    dip   = p["uturn_dip"]

    # Circumradii from outermost → innermost
    rings: list[float] = [R_max - i * d for i in range(N)]

    all_pts: list[float] = []

    for i, R in enumerate(rings):

        # ── Ring traversal ─────────────────────────────────────────
        seg = ring_cw(R) if i % 2 == 0 else ring_ccw(R)
        append_segment(all_pts, seg)

        # ── U-turn to next ring (skip on last ring) ────────────────
        if i < N - 1:
            R_next = rings[i + 1]
            if i % 2 == 0:
                # CW ring ends at lower-right (vertex 5)
                A = hex_pt(R,      5)
                B = hex_pt(R_next, 5)
            else:
                # CCW ring ends at lower-left (vertex 4)
                A = hex_pt(R,      4)
                B = hex_pt(R_next, 4)

            append_segment(all_pts, bezier_uturn(A, B, dip))

    return all_pts


# ─────────────────────────────────────────────────────────────────
# Design metadata
# ─────────────────────────────────────────────────────────────────

DESIGN_META = {
    "name":   "hex_spiral_heater",
    "title":  "Hexagonal Spiral Microheater",
    "layer":  "MICROHEATER",
    "units":  "micrometers",
    "description": (
        "8 concentric flat-top hexagonal rings (100 µm → 30 µm), "
        "10 µm ring spacing, smooth Bezier U-turns at bottom."
    ),
}


# ─────────────────────────────────────────────────────────────────
# Self-test (no AutoCAD needed)
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pts    = build_path()
    n      = len(pts) // 2
    xs, ys = pts[0::2], pts[1::2]

    from config import HEX_SPIRAL_PARAMS as P
    rings = [P["R_max"] - i * P["ring_spacing"] for i in range(P["n_rings"])]

    print(f"Total vertices : {n}")
    print(f"X range        : {min(xs):.1f}  …  {max(xs):.1f}  µm")
    print(f"Y range        : {min(ys):.1f}  …  {max(ys):.1f}  µm")
    print()
    for i, R in enumerate(rings):
        H    = math.sqrt(3) / 2
        cw   = i % 2 == 0
        sv   = hex_pt(R, 4 if cw else 5)
        ev   = hex_pt(R, 5 if cw else 4)
        dirn = "CW " if cw else "CCW"
        print(f"  Ring {i}  R={R:6.1f} µm  {dirn}  "
              f"start=({sv[0]:7.2f}, {sv[1]:7.2f})  "
              f"end=({ev[0]:7.2f}, {ev[1]:7.2f})")
