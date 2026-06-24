"""
src/utils.py — Shared utilities: file naming, path handling, printing helpers.
"""

from __future__ import annotations
import os
import sys
from datetime import datetime


# ─────────────────────────────────────────────
# Console helpers
# ─────────────────────────────────────────────

def print_header(title: str) -> None:
    """Print a formatted section header."""
    bar = "─" * (len(title) + 4)
    print(f"\n┌{bar}┐")
    print(f"│  {title}  │")
    print(f"└{bar}┘")


def print_ok(msg: str) -> None:
    print(f"  ✅  {msg}")


def print_info(msg: str) -> None:
    print(f"  ℹ️   {msg}")


def print_err(msg: str) -> None:
    print(f"  ❌  {msg}", file=sys.stderr)


# ─────────────────────────────────────────────
# File / path helpers
# ─────────────────────────────────────────────

def make_save_path(saves_dir: str, design_name: str, ext: str) -> str:
    """
    Build a timestamped output path inside *saves_dir*.

    Example
    -------
    make_save_path(r"D:\\AUTOCAD_ENGINE\\saves", "microheater", "dwg")
    → "D:\\AUTOCAD_ENGINE\\saves\\microheater_2026-06-24_153045.dwg"
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename  = f"{design_name}_{timestamp}.{ext.lstrip('.')}"
    os.makedirs(saves_dir, exist_ok=True)
    return os.path.join(saves_dir, filename)


def ensure_dir(path: str) -> None:
    """Create *path* (and parents) if it does not exist."""
    os.makedirs(path, exist_ok=True)
