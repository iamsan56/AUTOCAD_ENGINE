"""
src/layers.py — Layer setup helpers for AutoCAD COM and ezdxf engines.
"""

from __future__ import annotations
from typing import Any, Dict

# Config is imported lazily so this module can be imported standalone
def setup_layers_com(doc: Any, layers_config: Dict[str, Dict]) -> None:
    """
    Create or update layers in an open AutoCAD document (COM / pywin32).

    Parameters
    ----------
    doc           : AutoCAD Document COM object (acad.ActiveDocument)
    layers_config : dict from config.LAYERS, e.g.
                    {"MICROHEATER": {"color": 5, "linetype": "Continuous"}, …}
    """
    for name, props in layers_config.items():
        # Try to get existing layer; create if absent
        try:
            layer = doc.Layers.Item(name)
        except Exception:
            layer = doc.Layers.Add(name)

        layer.Color = props.get("color", 7)

        # Linetype "Continuous" is always present – no need to load it
        linetype_name = props.get("linetype", "Continuous")
        try:
            # Load the linetype into the document first (safe no-op if already loaded)
            if linetype_name != "Continuous":
                doc.Linetypes.Load(linetype_name, "acad.lin")
            layer.Linetype = linetype_name
        except Exception:
            pass  # Silently skip if linetype not found; keep default


def setup_layers_dxf(doc: Any, layers_config: Dict[str, Dict]) -> None:
    """
    Create layers in an ezdxf document.

    Parameters
    ----------
    doc           : ezdxf Drawing object (returned by ezdxf.new())
    layers_config : dict from config.LAYERS
    """
    for name, props in layers_config.items():
        if name not in doc.layers:
            doc.layers.new(name=name, dxfattribs={
                "color":    props.get("color", 7),
                "linetype": props.get("linetype", "Continuous"),
            })
