"""
main.py — AutoCAD Engine Entry Point

Presents an interactive menu so the user can pick which design to draw
and which format to save, then opens AutoCAD and executes the macro.

Usage
-----
    # Interactive mode (recommended):
    python main.py

    # CLI mode (non-interactive):
    python main.py --design microheater --format dwg
    python main.py --design hex_spiral_heater --format both
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

# ── Make sure project root is on sys.path ──────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config         import LAYERS, SAVES_DIR, INSUNITS
from src.cad_engine import AutoCADEngine
from src.utils      import print_header, print_ok, print_info, print_err, make_save_path

# ─────────────────────────────────────────────────────────────────
# Design registry  {display_name: module_path}
# ─────────────────────────────────────────────────────────────────
DESIGN_REGISTRY: dict[str, str] = {
    "microheater":          "designs.microheater",
    "hex_spiral_heater":    "designs.hex_spiral_heater",
    "reference_hex_heater": "designs.reference_hex_heater",
    "wavy_hexagon":         "designs.wavy_hexagon",
    "rectified_hexagon":    "designs.rectified_hexagon",
    "rectified_reference_hex": "designs.rectified_reference_hex",
    "rectified_hex_spiral": "designs.rectified_hex_spiral",
    "large_hex_spiral":     "designs.large_hex_spiral",
}

DESIGN_LABELS: dict[str, str] = {
    "microheater":          "[1] Standard Microheater (Wavy Serpentine)",
    "hex_spiral_heater":    "[2] Hexagonal Spiral Microheater (Double-Pass Serpentine)",
    "reference_hex_heater": "[3] Reference Hexagonal Heater (Straight Serpentine)",
    "wavy_hexagon":         "[4] Wavy Hexagon",
    "rectified_hexagon":    "[5] Rectified (Semi-circle) Hexagon",
    "rectified_reference_hex": "[6] Rectified Reference Serpentine",
    "rectified_hex_spiral": "[7] Rectified Hexagonal Spiral (Full-Wave)",
    "large_hex_spiral":     "[8] Large Straight Double Hexagonal Spiral",
}

FORMAT_OPTIONS = [
    ("1", "dwg",  "DWG  — AutoCAD native format"),
    ("2", "dxf",  "DXF  — text-based, universal format"),
    ("3", "both", "Both DWG and DXF"),
]


# ─────────────────────────────────────────────────────────────────
# Interactive menus
# ─────────────────────────────────────────────────────────────────

def interactive_select_design() -> str:
    """Show numbered design list and return the chosen design key."""
    designs = list(DESIGN_REGISTRY.keys())

    print()
    print("  ┌─────────────────────────────────────────────────────┐")
    print("  │            Which design do you want?                │")
    print("  └─────────────────────────────────────────────────────┘")
    print()

    for i, key in enumerate(designs, start=1):
        mod  = importlib.import_module(DESIGN_REGISTRY[key])
        meta = getattr(mod, "DESIGN_META", {})
        label = DESIGN_LABELS.get(key, key)
        desc  = meta.get("description", "")
        # Wrap description to 55 chars
        desc_short = (desc[:58] + "…") if len(desc) > 60 else desc
        print(f"    [{i}]  {label}")
        print(f"         {desc_short}")
        print()

    while True:
        try:
            raw = input("  Enter number: ").strip()
            idx = int(raw) - 1
            if 0 <= idx < len(designs):
                chosen = designs[idx]
                print(f"\n  ✅  Selected: {DESIGN_LABELS[chosen]}\n")
                return chosen
            print(f"  ⚠️   Please enter a number between 1 and {len(designs)}.")
        except (ValueError, EOFError):
            print("  ⚠️   Invalid input — please enter a number.")
        except KeyboardInterrupt:
            print("\n  Cancelled.")
            sys.exit(0)


def interactive_select_format() -> str:
    """Show format options and return the chosen format string."""
    print("  ┌─────────────────────────────────────────────────────┐")
    print("  │              Which format to save?                  │")
    print("  └─────────────────────────────────────────────────────┘")
    print()
    for num, key, label in FORMAT_OPTIONS:
        print(f"    [{num}]  {label}")
    print()

    while True:
        try:
            raw = input("  Enter number [1]: ").strip() or "1"
            for num, key, label in FORMAT_OPTIONS:
                if raw == num:
                    print(f"\n  ✅  Format: {label}\n")
                    return key
            print("  ⚠️   Please enter 1, 2, or 3.")
        except (EOFError, KeyboardInterrupt):
            print("\n  Defaulting to DWG.")
            return "dwg"


# ─────────────────────────────────────────────────────────────────
# List designs (for --list flag)
# ─────────────────────────────────────────────────────────────────

def list_designs() -> None:
    print_header("Registered Designs")
    for key, module in DESIGN_REGISTRY.items():
        mod  = importlib.import_module(module)
        meta = getattr(mod, "DESIGN_META", {})
        print(f"  • {key:22s}  {meta.get('title', key)}")
        print(f"    {'':22s}  {meta.get('description', '')[:70]}")
        print()


# ─────────────────────────────────────────────────────────────────
# Core drawing routine
# ─────────────────────────────────────────────────────────────────

def run_design(design_name: str, fmt: str) -> None:
    """Open AutoCAD, draw *design_name*, save in *fmt* format."""

    if design_name not in DESIGN_REGISTRY:
        print_err(
            f"Unknown design '{design_name}'. "
            f"Available: {', '.join(DESIGN_REGISTRY)}"
        )
        sys.exit(1)

    mod  = importlib.import_module(DESIGN_REGISTRY[design_name])
    meta = getattr(mod, "DESIGN_META", {"name": design_name, "layer": "MICROHEATER"})

    print_header(f"AutoCAD Engine  →  {meta.get('title', design_name)}")

    # ── Generate geometry ──────────────────────────────────────────
    print_info("Generating geometry …")
    path_pts = mod.build_path()
    n_verts  = len(path_pts) // 2
    print_ok(f"Path generated: {n_verts} vertices")

    # ── Open AutoCAD & draw ────────────────────────────────────────
    with AutoCADEngine() as cad:
        cad.new_drawing()
        cad.set_units(INSUNITS)
        cad.setup_layers(LAYERS)

        layer = meta.get("layer", "MICROHEATER")
        cad.draw_lwpolyline(path_pts, layer=layer, width=0.0)
        print_ok(f"Design drawn on layer '{layer}' (colour: White)")

        cad.regen()
        cad.zoom_extents()

        # ── Save ──────────────────────────────────────────────────
        formats_to_save = ["dwg", "dxf"] if fmt == "both" else [fmt]
        saved_paths: list[str] = []

        for f in formats_to_save:
            sp = make_save_path(SAVES_DIR, design_name, f)
            cad.save(sp, fmt=f)
            saved_paths.append(sp)

    # ── Summary ────────────────────────────────────────────────────
    print()
    print_header("Done")
    for sp in saved_paths:
        print_ok(f"Saved → {sp}")
    print_info(f"Folder : {SAVES_DIR}")
    print()


# ─────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog        = "python main.py",
        description = "AutoCAD Engine — draw parametric designs and save as DWG/DXF.",
    )
    parser.add_argument("--design", "-d", default=None,
                        help="Design key (skip interactive menu)")
    parser.add_argument("--format", "-f", default=None,
                        choices=["dwg", "dxf", "both"],
                        help="Output format (skip interactive menu)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all registered designs and exit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list:
        list_designs()
        return

    # ── Banner ─────────────────────────────────────────────────────
    print()
    print("  ╔═══════════════════════════════════════════════════╗")
    print("  ║           A U T O C A D   E N G I N E            ║")
    print("  ║         Python → COM Macro Automation            ║")
    print("  ╚═══════════════════════════════════════════════════╝")

    # ── Design selection ───────────────────────────────────────────
    design = args.design if args.design else interactive_select_design()

    # Validate early
    if design not in DESIGN_REGISTRY:
        print_err(f"Unknown design '{design}'. Run with --list to see options.")
        sys.exit(1)

    # ── Format selection ───────────────────────────────────────────
    fmt = args.format if args.format else interactive_select_format()

    # ── Execute ────────────────────────────────────────────────────
    run_design(design, fmt)


if __name__ == "__main__":
    main()
