"""
main.py — AutoCAD Engine Entry Point

Opens AutoCAD, draws the selected design, and saves the output file.

Usage
-----
    python main.py
    python main.py --design microheater
    python main.py --design microheater --format dxf
    python main.py --design microheater --format dwg
    python main.py --design microheater --format both
    python main.py --list

Requirements
------------
    pip install pywin32
"""

from __future__ import annotations
import argparse
import importlib
import os
import sys

# ── Make sure project root is on sys.path so absolute imports work ──
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config         import LAYERS, MICROHEATER_PARAMS, HEX_SPIRAL_PARAMS, SAVES_DIR, INSUNITS
from src.cad_engine import AutoCADEngine
from src.utils      import print_header, print_ok, print_info, print_err, make_save_path

# ─────────────────────────────────────────────
# Registry of available designs
# ─────────────────────────────────────────────
DESIGN_REGISTRY: dict[str, str] = {
    "microheater":       "designs.microheater",       # Mirrored Wavy Microheater
    "hex_spiral_heater": "designs.hex_spiral_heater", # Hexagonal Spiral Microheater
}


def list_designs() -> None:
    """Print all registered designs."""
    print_header("Available Designs")
    for name, module in DESIGN_REGISTRY.items():
        mod = importlib.import_module(module)
        meta = getattr(mod, "DESIGN_META", {})
        print(f"  • {name:20s}  {meta.get('description', '')}")
    print()


# ─────────────────────────────────────────────
# Core drawing routine
# ─────────────────────────────────────────────

def run_design(design_name: str, fmt: str) -> None:
    """
    Load *design_name*, open AutoCAD, draw the design, and save.

    Parameters
    ----------
    design_name : key in DESIGN_REGISTRY (e.g. "microheater")
    fmt         : "dwg", "dxf", or "both"
    """
    # ── Load design module ───────────────────────────────────────
    if design_name not in DESIGN_REGISTRY:
        print_err(
            f"Unknown design '{design_name}'. "
            f"Available: {', '.join(DESIGN_REGISTRY.keys())}"
        )
        sys.exit(1)

    module_path = DESIGN_REGISTRY[design_name]
    mod         = importlib.import_module(module_path)
    meta        = getattr(mod, "DESIGN_META", {"name": design_name, "layer": "0"})

    print_header(f"AutoCAD Engine  →  {meta.get('title', design_name)}")

    # ── Generate geometry ────────────────────────────────────────
    print_info("Generating geometry …")
    path_pts  = mod.build_path()          # flat [x,y,…] centrelinearray
    markers   = mod.get_terminal_markers() if hasattr(mod, "get_terminal_markers") else []

    n_verts = len(path_pts) // 2
    print_ok(f"Path generated: {n_verts} vertices")

    # ── Open AutoCAD & draw ──────────────────────────────────────
    with AutoCADEngine() as cad:
        cad.new_drawing()
        cad.set_units(INSUNITS)
        cad.setup_layers(LAYERS)

        # Draw main heater path
        layer = meta.get("layer", "MICROHEATER")
        cad.draw_lwpolyline(path_pts, layer=layer, width=0.0)
        print_ok(f"Microheater path drawn on layer '{layer}'")

        # Draw terminal markers and labels
        for m in markers:
            cad.draw_circle(m["cx"], m["cy"], m["radius"], layer="MARKERS")
            cad.draw_text(m["label"], m["lx"], m["ly"],
                          height=MICROHEATER_PARAMS["label_height"],
                          layer="LABELS")
        if markers:
            print_ok(f"Terminal markers added: {[m['label'] for m in markers]}")

        # Title text — placed above the geometry using design-specific offset
        title    = meta.get("title", design_name)
        title_x  = meta.get("title_x", -55)
        title_y  = meta.get("title_y",  95)
        title_h  = meta.get("title_height", MICROHEATER_PARAMS["title_height"])
        cad.draw_text(title, x=title_x, y=title_y, height=title_h, layer="LABELS")

        cad.regen()
        cad.zoom_extents()

        # ── Save ─────────────────────────────────────────────────
        formats_to_save = []
        if fmt == "both":
            formats_to_save = ["dwg", "dxf"]
        else:
            formats_to_save = [fmt]

        saved_paths: list[str] = []
        for f in formats_to_save:
            save_path = make_save_path(SAVES_DIR, design_name, f)
            cad.save(save_path, fmt=f)
            saved_paths.append(save_path)

    print()
    print_header("Done")
    for sp in saved_paths:
        print_ok(f"Output  → {sp}")
    print_info(f"Saves folder: {SAVES_DIR}")
    print()


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog        = "python main.py",
        description = "AutoCAD Engine – draw and save parametric CAD designs.",
    )
    parser.add_argument(
        "--design", "-d",
        default = "microheater",
        help    = "Design name to draw (default: microheater)",
    )
    parser.add_argument(
        "--format", "-f",
        default  = "dwg",
        choices  = ["dwg", "dxf", "both"],
        help     = "Output format: dwg | dxf | both (default: dwg)",
    )
    parser.add_argument(
        "--list", "-l",
        action  = "store_true",
        help    = "List all available designs and exit",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list:
        list_designs()
        return

    run_design(args.design, args.format)


if __name__ == "__main__":
    main()
