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
    "wave_amplitude": 5.0,      # µm – perpendicular half-amplitude of sinusoidal wave
    "wave_period":   10.0,      # µm – one full cycle length along path

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
HEX_SPIRAL_PARAMS = {
    "R_max":         100.0,  # µm – outermost ring circumradius (center → vertex)
    "n_rings":         8,    # number of concentric hexagonal rings
    "ring_spacing":   10.0,  # µm – radial gap between adjacent ring centrelines
    "uturn_dip":       3.0,  # µm – how far the bottom U-turns dip below hex vertex
    "track_width":     3.0,  # µm
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
DXF_VERSION = "R2010"   # ezdxf version string (standalone mode)
INSUNITS    = 6         # AutoCAD drawing units: 6 = micrometers
