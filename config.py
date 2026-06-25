"""
config.py — Global Configuration for AutoCAD Engine
All units are in micrometers (µm) unless otherwise noted.
"""

import os

# ─────────────────────────────────────────────
# Project Paths  (auto-detected — works on any machine)
# ─────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SAVES_DIR    = os.path.join(PROJECT_ROOT, "saves")

# ─────────────────────────────────────────────
# Microheater Design Parameters
# ─────────────────────────────────────────────
MICROHEATER_PARAMS = {
    # Wave shape
    "wave_amplitude": 5.0,      # µm
    "wave_period":   10.0,      # µm

    # Heater track reference
    "track_width":   3.0,       # µm

    # Terminal coordinates
    "in_x":  -40.0,  "in_y":  0.0,
    "out_x":   0.0,  "out_y": 0.0,

    # Main path geometry
    "outer_left_x":  -40.0,
    "outer_right_x":  40.0,
    "top_y":          82.0,
    "inner_left_x":  -20.0,
    "inner_right_x":  20.0,
    "inner_top_y":    70.0,
    "lower_y":        15.0,
}

# ─────────────────────────────────────────────
# Hexagonal Spiral Microheater Parameters
# ─────────────────────────────────────────────
#
# Each "ring band" is the space between two concentric hexagons.
# The path makes TWO passes per band (outer track + inner track),
# creating the double-line look on each hexagonal face.
#
#   band_pitch = track_separation + ring_gap
#   Ring i outer:  R_max - i * band_pitch
#   Ring i inner:  R_max - i * band_pitch - track_separation
#
HEX_SPIRAL_PARAMS = {
    "R_max":              100.0,   # µm – circumradius of outermost hexagon
    "n_rings":              6,     # number of double-pass ring bands
    "track_separation":     7.0,   # µm – gap between outer/inner tracks within one band
    "ring_gap":             5.0,   # µm – visible gap between consecutive bands
    "uturn_bulge":          4.0,   # µm – outward bulge of U-turn curves at bottom
    "lead_length":         15.0,   # µm – length of IN/OUT terminal leads
}

# ─────────────────────────────────────────────
# Hexagonal Microheater Reference Design Parameters
# ─────────────────────────────────────────────
# Pointy-top hexagon with a single continuous serpentine path.
# N tracks total, U-turns at the 210° gap axis, and a central return line.
REFERENCE_HEX_PARAMS = {
    "R_max":         100.0,   # µm – circumradius of outermost hexagon
    "n_tracks":        7,     # number of tracks
    "spacing":         8.0,   # µm – radial distance between adjacent tracks
    "gap_width":      24.0,   # µm – width of the clearance gap at 210°
    "lead_length":    30.0,   # µm – length of IN/OUT terminal leads extending from the gap
}

# ─────────────────────────────────────────────
# Wavy Hexagon Parameters
# ─────────────────────────────────────────────
WAVY_HEXAGON_PARAMS = {
    "radius":         100.0,   # µm – circumradius of the hexagon
    "amplitude":        5.0,   # µm – peak amplitude of the sine wave along the edges
    "period":          20.0,   # µm – length of one full sine wave cycle
}

# ─────────────────────────────────────────────
# Rectified Hexagon Parameters
# ─────────────────────────────────────────────
RECTIFIED_HEXAGON_PARAMS = {
    "radius":         100.0,   # µm – circumradius of the hexagon
    "amplitude":        5.0,   # µm – peak amplitude of the rectified semi-circles
    "period":          10.0,   # µm – length of one full semi-circle bump
    "outward_bumps":   True,   # True = bumps point away from center, False = towards center
}

# ─────────────────────────────────────────────
# Layer Definitions
# ─────────────────────────────────────────────
# AutoCAD Color Index (ACI):
#   1=Red  2=Yellow  3=Green  4=Cyan  5=Blue  6=Magenta  7=White
LAYERS = {
    "MICROHEATER": {"color": 7, "linetype": "Continuous"},  # White – heater path
}

# ─────────────────────────────────────────────
# Drawing Settings
# ─────────────────────────────────────────────
DXF_VERSION = "R2010"
INSUNITS    = 6   # 6 = micrometers
