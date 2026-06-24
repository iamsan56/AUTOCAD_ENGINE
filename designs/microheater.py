"""
designs/microheater.py — Mirrored Wavy Microheater (Perfect Symmetric Topology)

Generates the complete centerline path of the microheater as a continuous
flat coordinate array [x1,y1, x2,y2, …] ready for:
  • AutoCAD COM  → cad_engine.draw_lwpolyline(pts)
  • ezdxf        → msp.add_lwpolyline(pts)

Design Topology (all coordinates in µm)
────────────────────────────────────────
                ┌─────────── wavy top ───────────┐
                │                                │
          ┌─────┘  inner                         └─────┐
          │         U-turns                            │
    IN ───┘         ───────                       ┌────┘
   (-40,0)         │       │                    (-20,15)→(-10,15)
                   │       │                              │
                   └───────┘                          OUT (0,0)
                   (inner serpentine)

Full path: IN(-40,0) → up-left(wavy) → top(wavy) → down-right(wavy)
           → U-turn → up-inner-right(wavy) → top-U-turn
           → down-inner-left(wavy) → U-turn → short-down → OUT(0,0)
"""

from __future__ import annotations
import math
import sys
import os

# Allow running this file directly for quick geometry checks
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.shapes import wavy_pts, arc_pts, circle_marker_pts, append_segment
from config import MICROHEATER_PARAMS


# ─────────────────────────────────────────────────────────────────
# Path builder
# ─────────────────────────────────────────────────────────────────

def build_path(params: dict | None = None) -> list[float]:
    """
    Build the complete microheater centreline as a flat [x,y,…] list.

    Segment map
    -----------
    1.  Wavy UP   (-40, 0) → (-40, 82)   outer-left vertical
    2.  Wavy →    (-40,82) → ( 40, 82)   top horizontal run
    3.  Wavy DOWN ( 40,82) → ( 40, 15)   outer-right vertical
    4.  Arc ⌒     ( 40,15) → ( 20, 15)   bottom-right U-turn (dips to y=5)
    5.  Wavy UP   ( 20,15) → ( 20, 70)   inner-right vertical
    6.  Arc ⌢     ( 20,70) → (-20, 70)   top-inner  U-turn (peaks at y=90)
    7.  Wavy DOWN (-20,70) → (-20, 15)   inner-left vertical
    8.  Arc ⌒     (-20,15) → (  0, 15)   bottom-center U-turn (dips to y=5)
    9.  Wavy DOWN (  0,15) → (  0,  0)   short exit column → OUT
    """
    p   = params or MICROHEATER_PARAMS
    amp = p["wave_amplitude"]
    per = p["wave_period"]

    all_pts: list[float] = []

    # ── 1. Outer-left vertical: (-40, 0) → (-40, 82)  UP ──────
    append_segment(all_pts,
        wavy_pts(-40, 0, -40, 82, amp, per, n_points=200))

    # ── 2. Top horizontal:     (-40,82) → ( 40, 82)  RIGHT ────
    append_segment(all_pts,
        wavy_pts(-40, 82, 40, 82, amp, per, n_points=200))

    # ── 3. Outer-right vertical: (40,82) → (40, 15)  DOWN ─────
    append_segment(all_pts,
        wavy_pts(40, 82, 40, 15, amp, per, n_points=165))

    # ── 4. Bottom-right U-turn: (40,15) → (20,15) ─────────────
    #    Centre (30,15), r=10, clockwise from 0° to -180°
    #    Lowest point at t=0.5: angle=-90° → (30, 5)
    append_segment(all_pts,
        arc_pts(30, 15, 10, 0, -math.pi, n_points=40))

    # ── 5. Inner-right vertical: (20,15) → (20,70)   UP ───────
    append_segment(all_pts,
        wavy_pts(20, 15, 20, 70, amp, per, n_points=140))

    # ── 6. Top-inner U-turn: (20,70) → (-20,70) ───────────────
    #    Centre (0,70), r=20, CCW from 0° to 180°
    #    Highest point at t=0.5: angle=90° → (0, 90)
    append_segment(all_pts,
        arc_pts(0, 70, 20, 0, math.pi, n_points=60))

    # ── 7. Inner-left vertical: (-20,70) → (-20,15)  DOWN ─────
    append_segment(all_pts,
        wavy_pts(-20, 70, -20, 15, amp, per, n_points=140))

    # ── 8. Bottom-center U-turn: (-20,15) → (0,15) ────────────
    #    Centre (-10,15), r=10
    #    p1=(-20,15) angle=180°, p2=(0,15) angle=0°(=360°)
    #    CCW from π to 2π passes through 3π/2 (270°) = dips to y=5 ✓
    append_segment(all_pts,
        arc_pts(-10, 15, 10, math.pi, 2 * math.pi, n_points=40))

    # ── 9. Short exit column: (0,15) → (0,0)  OUT ─────────────
    append_segment(all_pts,
        wavy_pts(0, 15, 0, 0, amp / 2, per, n_points=30))

    return all_pts


# ─────────────────────────────────────────────────────────────────
# Terminal markers (small circles at IN and OUT)
# ─────────────────────────────────────────────────────────────────

def get_terminal_markers(params: dict | None = None) -> list[dict]:
    """
    Return marker definitions for the IN and OUT terminals.

    Each entry: {"cx": …, "cy": …, "radius": …, "label": …, "lx": …, "ly": …}
    """
    p = params or MICROHEATER_PARAMS
    r = p["track_width"]   # marker radius = track width for visibility
    return [
        {
            "cx": p["in_x"],  "cy": p["in_y"],
            "radius": r,
            "label": "IN",
            "lx": p["in_x"]  - 10,
            "ly": p["in_y"]  - 5,
        },
        {
            "cx": p["out_x"], "cy": p["out_y"],
            "radius": r,
            "label": "OUT",
            "lx": p["out_x"] + 2,
            "ly": p["out_y"] - 5,
        },
    ]


# ─────────────────────────────────────────────────────────────────
# Design metadata
# ─────────────────────────────────────────────────────────────────

DESIGN_META = {
    "name":        "microheater",
    "title":       "Mirrored Wavy Microheater – Perfect Symmetric Topology",
    "layer":       "MICROHEATER",
    "units":       "micrometers",
    "description": (
        "Serpentine microheater with sinusoidal wave pattern. "
        "IN at (-40,0) µm, OUT at (0,0) µm. "
        "Wave amplitude 5 µm, period 10 µm."
    ),
}


# ─────────────────────────────────────────────────────────────────
# Quick self-test: print path stats when run directly
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pts = build_path()
    n_vertices = len(pts) // 2
    xs = pts[0::2]
    ys = pts[1::2]
    print(f"Total vertices : {n_vertices}")
    print(f"X range        : {min(xs):.2f} … {max(xs):.2f} µm")
    print(f"Y range        : {min(ys):.2f} … {max(ys):.2f} µm")
    print(f"First point    : ({xs[0]:.2f}, {ys[0]:.2f})  ← should be IN  (-40, 0)")
    print(f"Last  point    : ({xs[-1]:.2f}, {ys[-1]:.2f})  ← should be OUT (  0, 0)")
