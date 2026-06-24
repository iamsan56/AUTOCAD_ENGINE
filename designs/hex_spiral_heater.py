"""
designs/hex_spiral_heater.py — Hexagonal Spiral Microheater (Double-Pass)

Each ring BAND sits between two concentric hexagons (outer track, inner track).
The path makes TWO passes per band — once along the outer hex, once along the
inner hex — creating the characteristic double-line look on every face.

Flat-top hexagon vertex layout (circumradius R)
────────────────────────────────────────────────
         V2 ─────── V1
        /               \\
      V3                 V0   ← (R, 0)
        \\               /
         V4 ─────── V5
              ↑  ↑
          gap face (bottom)

  idx : angle : position
   0  :   0°  : right
   1  :  60°  : upper-right
   2  : 120°  : upper-left
   3  : 180°  : left
   4  : 240°  : lower-left   ← IN terminal / ring transitions
   5  : 300°  : lower-right  ← U-turn outer↔inner

Path through ONE ring band
──────────────────────────
  Outer pass (CW, 5 sides):
    V4_out → V3_out → V2_out → V1_out → V0_out → V5_out

  U-turn at V5 (outer → inner, curving outward):
    V5_out ⟶ V5_in

  Inner pass (CCW, 5 sides):
    V5_in → V0_in → V1_in → V2_in → V3_in → V4_in

  The bottom face (V4↔V5) is the GAP — it's where the U-turn and
  inter-ring transitions live.

Per-face result (5 of 6 faces):
  Two parallel lines — outer track + inner track — with a visible gap
  between them (= track_separation).

Ring-to-ring transition (at V4, left side of gap):
  V4_in of ring i  ⟶  V4_out of ring i+1
  This is a small bezier curving outward (radially away from center).

Terminal leads:
  IN  = short line extending outward from V4 of outermost outer hex
  OUT = short line extending outward from V4 of innermost inner hex
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
    """
    Vertex of a flat-top regular hexagon.
    idx 0-5: 0=right (0°), going CCW by 60° increments.
    """
    angle = math.radians(60 * idx)
    return (R * math.cos(angle), R * math.sin(angle))


def hex_pts_flat(R: float, indices: list[int]) -> list[float]:
    """Return a flat [x,y,x,y,...] list for the given vertex indices at radius R."""
    pts: list[float] = []
    for idx in indices:
        x, y = hex_pt(R, idx)
        pts.extend([x, y])
    return pts


def radial_uturn(
    A: tuple[float, float],
    B: tuple[float, float],
    bulge: float,
    n: int = 20,
) -> list[float]:
    """
    Quadratic Bézier from A to B, bulging *radially outward* from the
    hexagon centre (origin).

    The control point is placed at the midpoint of A and B, shifted
    outward along the radial direction by *bulge* µm.
    """
    mx = (A[0] + B[0]) / 2.0
    my = (A[1] + B[1]) / 2.0
    dist = math.hypot(mx, my)
    if dist > 1e-9:
        nx, ny = mx / dist, my / dist          # radial outward unit vector
    else:
        nx, ny = 0.0, -1.0                     # fallback: downward

    cx = mx + bulge * nx
    cy = my + bulge * ny

    pts: list[float] = []
    for i in range(n + 1):
        t  = i / n
        mt = 1.0 - t
        x  = mt * mt * A[0] + 2.0 * mt * t * cx + t * t * B[0]
        y  = mt * mt * A[1] + 2.0 * mt * t * cy + t * t * B[1]
        pts.extend([x, y])
    return pts


# ─────────────────────────────────────────────────────────────────
# Main path builder
# ─────────────────────────────────────────────────────────────────

def build_path(params: dict | None = None) -> list[float]:
    """
    Build the complete hexagonal serpentine spiral as a flat [x,y,...] list.

    Structure for N ring bands:
      [IN lead] →
        Band 0: outer CW → U-turn V5 → inner CCW → transition V4 →
        Band 1: outer CW → U-turn V5 → inner CCW → transition V4 →
        …
        Band N-1: outer CW → U-turn V5 → inner CCW
      → [OUT lead]
    """
    p           = params or HEX_SPIRAL_PARAMS
    R_max       = p["R_max"]
    N           = p["n_rings"]
    track_sep   = p["track_separation"]
    ring_gap    = p["ring_gap"]
    bulge       = p["uturn_bulge"]
    lead_len    = p.get("lead_length", 15.0)

    band_pitch = track_sep + ring_gap        # radial step between successive outer tracks

    all_pts: list[float] = []

    # ── IN terminal lead ──────────────────────────────────────────
    # Extends outward from V4 of outermost outer hex at 240°
    start = hex_pt(R_max, 4)
    lead_angle = math.radians(240)
    lead_tip = (
        start[0] + lead_len * math.cos(lead_angle),
        start[1] + lead_len * math.sin(lead_angle),
    )
    all_pts.extend([lead_tip[0], lead_tip[1], start[0], start[1]])

    # ── Ring bands ────────────────────────────────────────────────
    for i in range(N):
        R_out = R_max - i * band_pitch
        R_in  = R_out - track_sep

        # --- Outer pass (CW): V4 → V3 → V2 → V1 → V0 → V5 ------
        # 5 sides of the hexagon, skipping the bottom face V5→V4
        outer = hex_pts_flat(R_out, [4, 3, 2, 1, 0, 5])
        append_segment(all_pts, outer)

        # --- U-turn at V5: outer → inner (curving outward) --------
        A = hex_pt(R_out, 5)
        B = hex_pt(R_in,  5)
        append_segment(all_pts, radial_uturn(A, B, bulge))

        # --- Inner pass (CCW): V5 → V0 → V1 → V2 → V3 → V4 -----
        # 5 sides going the other way
        inner = hex_pts_flat(R_in, [5, 0, 1, 2, 3, 4])
        append_segment(all_pts, inner)

        # --- Transition to next ring at V4 (curving outward) ------
        if i < N - 1:
            R_out_next = R_max - (i + 1) * band_pitch
            A = hex_pt(R_in,      4)
            B = hex_pt(R_out_next, 4)
            append_segment(all_pts, radial_uturn(A, B, bulge))

    # ── OUT terminal lead ─────────────────────────────────────────
    # Extends outward from V4 of innermost inner hex
    R_in_last = R_max - (N - 1) * band_pitch - track_sep
    end_pt = hex_pt(R_in_last, 4)
    lead_tip_out = (
        end_pt[0] + lead_len * math.cos(lead_angle),
        end_pt[1] + lead_len * math.sin(lead_angle),
    )
    all_pts.extend([lead_tip_out[0], lead_tip_out[1]])

    return all_pts


# ─────────────────────────────────────────────────────────────────
# Design metadata
# ─────────────────────────────────────────────────────────────────

DESIGN_META = {
    "name":   "hex_spiral_heater",
    "title":  "Hexagonal Spiral Microheater – Double-Pass Serpentine",
    "layer":  "MICROHEATER",
    "units":  "micrometers",
    "description": (
        "Concentric hexagonal ring bands with double-pass serpentine fill. "
        "6 bands, R=100→28 µm, 7 µm track separation, 5 µm ring gap. "
        "Each face shows 2 parallel lines; U-turns at bottom vertices."
    ),
}


# ─────────────────────────────────────────────────────────────────
# Self-test (no AutoCAD required)
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pts    = build_path()
    n      = len(pts) // 2
    xs, ys = pts[0::2], pts[1::2]

    from config import HEX_SPIRAL_PARAMS as P
    band_pitch = P["track_separation"] + P["ring_gap"]

    print(f"Total vertices : {n}")
    print(f"X range        : {min(xs):.1f}  …  {max(xs):.1f}  µm")
    print(f"Y range        : {min(ys):.1f}  …  {max(ys):.1f}  µm")
    print()

    for i in range(P["n_rings"]):
        R_out = P["R_max"] - i * band_pitch
        R_in  = R_out - P["track_separation"]
        print(f"  Band {i}:  R_out = {R_out:6.1f} µm   R_in = {R_in:6.1f} µm   "
              f"Δ = {R_out - R_in:.1f} µm")

    R_in_last = P["R_max"] - (P["n_rings"] - 1) * band_pitch - P["track_separation"]
    print(f"\n  Innermost inner R = {R_in_last:.1f} µm")
    print(f"  Total lines per face = {P['n_rings'] * 2}")
