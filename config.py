"""
config.py — Global Configuration for AutoCAD Engine
All units are in micrometers (µm) unless otherwise noted.
"""

import os

# ─────────────────────────────────────────────
# Project Paths
# ─────────────────────────────────────────────
PROJECT_ROOT = r"D:\AUTOCAD_ENGINE"
SAVES_DIR    = os.path.join(PROJECT_ROOT, "saves")

# ─────────────────────────────────────────────
# Microheater Design Parameters
# ─────────────────────────────────────────────
MICROHEATER_PARAMS = {
    # Wave shape
    "wave_amplitude": 5.0,      # µm – perpendicular half-amplitude of sinusoidal wave
    "wave_period":   10.0,      # µm – one full cycle length along path

    # Heater track reference (cosmetic, for future width-extrusion)
    "track_width":   3.0,       # µm

    # Terminal coordinates
    "in_x":  -40.0,  "in_y":  0.0,   # IN  terminal (leftmost)
    "out_x":   0.0,  "out_y": 0.0,   # OUT terminal (center)

    # Main path geometry
    "outer_left_x":  -40.0,   # x of outer-left vertical run
    "outer_right_x":  40.0,   # x of outer-right vertical run
    "top_y":          82.0,   # y of top horizontal run
    "inner_left_x":  -20.0,   # x of inner-left vertical run
    "inner_right_x":  20.0,   # x of inner-right vertical run
    "inner_top_y":    70.0,   # y of inner top U-turn
    "lower_y":        15.0,   # y of bottom U-turns

    # Text labels
    "label_height":   3.0,    # µm text height for IN / OUT labels
    "title_height":   4.0,    # µm text height for title
}

# ─────────────────────────────────────────────
# Layer Definitions
# ─────────────────────────────────────────────
# AutoCAD Color Index (ACI):
#   1=Red  2=Yellow  3=Green  4=Cyan  5=Blue  6=Magenta  7=White
LAYERS = {
    "MICROHEATER": {"color": 5, "linetype": "Continuous"},  # Blue  – heater path
    "LABELS":      {"color": 2, "linetype": "Continuous"},  # Yellow – IN / OUT text
    "MARKERS":     {"color": 1, "linetype": "Continuous"},  # Red   – terminal dots
}

# ─────────────────────────────────────────────
# Drawing Settings
# ─────────────────────────────────────────────
DXF_VERSION = "R2010"   # ezdxf version string (standalone mode)
INSUNITS    = 6         # AutoCAD drawing units: 6 = micrometers
