"""
src/shapes.py — Geometric Primitives for Microheater Path Generation

Provides:
  wavy_pts()      – sinusoidal segment between two points
  arc_pts()       – parametric circular arc
  circle_marker() – small circle at terminal points
"""

import math
from typing import List, Tuple


# ─────────────────────────────────────────────────────────────────
# Sinusoidal ("wavy") segment
# ─────────────────────────────────────────────────────────────────

def wavy_pts(
    x0: float, y0: float,
    x1: float, y1: float,
    amplitude: float,
    period: float,
    n_points: int = 200
) -> List[float]:
    """
    Generate a wavy polyline from (x0,y0) to (x1,y1).

    The sinusoidal wave oscillates *perpendicular* to the direction of travel,
    so a vertical segment waves left-right and a horizontal segment waves up-down.

    Returns
    -------
    list[float]
        Flat coordinate array  [x1,y1, x2,y2, … , xN,yN]
        ready for AutoCAD AddLightWeightPolyline / ezdxf add_lwpolyline.
    """
    length = math.hypot(x1 - x0, y1 - y0)
    if length < 1e-9:
        return [x0, y0]

    # Unit vector along path
    dx = (x1 - x0) / length
    dy = (y1 - y0) / length
    # Perpendicular unit vector (rotate 90° CCW)
    px = -dy
    py =  dx

    # Force the period to fit exactly into the edge length so the wave ends at 0
    num_cycles = max(1, round(length / period))
    actual_period = length / num_cycles

    pts: List[float] = []
    for i in range(n_points + 1):
        t     = i / n_points
        along = t * length
        wave  = amplitude * math.sin(2.0 * math.pi * along / actual_period)

        x = x0 + t * (x1 - x0) + wave * px
        y = y0 + t * (y1 - y0) + wave * py
        pts.extend([x, y])

    return pts


# ─────────────────────────────────────────────────────────────────
# Rectified Sinusoidal segment (Full wave rectifier)
# ─────────────────────────────────────────────────────────────────

def rectified_wave_pts(
    x0: float, y0: float,
    x1: float, y1: float,
    amplitude: float,
    period: float,
    n_points: int = 200,
    outward: bool = True,
    num_bumps: int | None = None
) -> List[float]:
    """
    Generate a full-wave rectified polyline (only positive semi-circle bumps) 
    from (x0,y0) to (x1,y1).
    """
    length = math.hypot(x1 - x0, y1 - y0)
    if length < 1e-9:
        return [x0, y0]

    # Unit vector along path
    dx = (x1 - x0) / length
    dy = (y1 - y0) / length
    
    # Perpendicular unit vector
    # For a CCW path, (-dy, dx) points inward. 
    # (dy, -dx) points outward.
    if outward:
        px, py = dy, -dx
    else:
        px, py = -dy, dx

    # Force the period to fit exactly into the edge length so the bump ends exactly at 0
    if num_bumps is None:
        num_bumps = max(1, round(length / period))
    actual_period = length / num_bumps

    # Ensure enough resolution for smooth semicircles (at least 30 points per bump)
    n_points = max(n_points, int(num_bumps * 30))

    pts: List[float] = []
    for i in range(n_points + 1):
        t     = i / n_points
        along = t * length
        # Absolute value of sine = full wave rectifier
        # We don't use 2.0*pi here because abs(sin) doubles the frequency!
        # If we want 'period' to represent one full bump width, we use pi*along/actual_period.
        wave  = amplitude * abs(math.sin(math.pi * along / actual_period))

        x = x0 + t * (x1 - x0) + wave * px
        y = y0 + t * (y1 - y0) + wave * py
        pts.extend([x, y])

    return pts


# ─────────────────────────────────────────────────────────────────
# Circular arc
# ─────────────────────────────────────────────────────────────────

def arc_pts(
    cx: float, cy: float,
    radius: float,
    start_angle: float,   # radians
    end_angle: float,     # radians  (sweep is always start → end linearly)
    n_points: int = 40
) -> List[float]:
    """
    Generate a circular arc as a flat coordinate array.

    The sweep goes *linearly* from start_angle to end_angle.
    Use negative end_angle (e.g. -π) for a clockwise sweep from 0°.

    Parameters
    ----------
    cx, cy       : arc centre
    radius       : arc radius
    start_angle  : starting angle in radians
    end_angle    : ending angle in radians (may cross 0 if negative)
    n_points     : number of segments (n_points+1 vertices)
    """
    pts: List[float] = []
    for i in range(n_points + 1):
        t = i / n_points
        a = start_angle + t * (end_angle - start_angle)
        pts.extend([cx + radius * math.cos(a),
                    cy + radius * math.sin(a)])
    return pts


# ─────────────────────────────────────────────────────────────────
# Small filled marker (approximated as a tiny closed circle polyline)
# ─────────────────────────────────────────────────────────────────

def circle_marker_pts(cx: float, cy: float, radius: float, n: int = 32) -> List[float]:
    """
    Return a flat list of points forming a small closed circle.
    Use with a closed LWPolyline to mark terminal points.
    """
    pts: List[float] = []
    for i in range(n + 1):
        a = 2.0 * math.pi * i / n
        pts.extend([cx + radius * math.cos(a),
                    cy + radius * math.sin(a)])
    return pts


# ─────────────────────────────────────────────────────────────────
# Convenience – append a segment to an existing flat list,
# skipping the first point (duplicate junction removal)
# ─────────────────────────────────────────────────────────────────

def append_segment(master: List[float], segment: List[float]) -> None:
    """Append *segment* to *master*, omitting the first x,y pair to avoid duplicates."""
    if master:
        master.extend(segment[2:])   # skip first (x, y) = indices 0 and 1
    else:
        master.extend(segment)
