"""
src/cad_engine.py — Live AutoCAD COM Bridge (pywin32 / win32com)

Wraps AutoCAD's COM (ActiveX) interface with a clean Python API.
Handles connection, layer setup, geometry drawing, and file saving.

Requirements
------------
  pip install pywin32
"""

from __future__ import annotations
import math
import os
import time
from typing import Dict, List, Optional, Any

import pythoncom
import win32com.client

from src.utils import print_ok, print_info, print_err


# ─────────────────────────────────────────────────────────────────
# Helper: build a COM-compatible VARIANT array from a flat float list
# ─────────────────────────────────────────────────────────────────

def _make_variant(flat_list: List[float]) -> Any:
    """Convert a flat [x,y,x,y,...] Python list to a COM VARIANT SafeArray."""
    return win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8,
        [float(v) for v in flat_list]
    )


def _make_point_variant(x: float, y: float, z: float = 0.0) -> Any:
    """Convert a 3-D point to a COM VARIANT (needed for AddText insertion)."""
    return win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8,
        [float(x), float(y), float(z)]
    )


# ─────────────────────────────────────────────────────────────────
# AutoCAD Engine class
# ─────────────────────────────────────────────────────────────────

class AutoCADEngine:
    """
    Live AutoCAD COM bridge.

    Usage (context manager)
    -----------------------
    with AutoCADEngine() as cad:
        cad.new_drawing()
        cad.draw_lwpolyline(pts, layer="MICROHEATER")
        cad.save("D:\\\\path\\\\out.dwg", fmt="dwg")
    """

    def __init__(self) -> None:
        self._acad:   Optional[Any] = None
        self._doc:    Optional[Any] = None
        self._mspace: Optional[Any] = None

    # ── Context manager ──────────────────────────────────────────

    def __enter__(self) -> "AutoCADEngine":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.disconnect()

    # ── Connection ───────────────────────────────────────────────

    def connect(self, create_if_not_exists: bool = True) -> "AutoCADEngine":
        """
        Connect to a running AutoCAD instance.
        If none is found and *create_if_not_exists* is True, launch AutoCAD.
        """
        pythoncom.CoInitialize()

        try:
            # Force Early Binding (solves dynamic dispatch AttributeError for .Add)
            self._acad = win32com.client.gencache.EnsureDispatch("AutoCAD.Application")
            print_ok("Connected to AutoCAD instance (Early Binding)")
        except Exception:
            try:
                self._acad = win32com.client.GetActiveObject("AutoCAD.Application")
                print_ok("Connected to existing AutoCAD instance (Late Binding)")
            except Exception:
                if not create_if_not_exists:
                    raise RuntimeError(
                        "AutoCAD is not running. "
                        "Start AutoCAD first, or pass create_if_not_exists=True."
                    )
                print_info("AutoCAD not found – launching …")
                self._acad = win32com.client.Dispatch("AutoCAD.Application")
                print_ok("AutoCAD launched successfully")
        
        self._acad.Visible = True
        
        # Give AutoCAD time to fully start up if it's launching
        for _ in range(10):
            try:
                _ = self._acad.Version
                break
            except Exception:
                time.sleep(1)
                
        return self

    def disconnect(self) -> None:
        """Release COM references."""
        self._mspace = None
        self._doc    = None
        self._acad   = None
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

    # ── Document management ──────────────────────────────────────

    def new_drawing(self, template: str = "") -> None:
        """Open a new drawing (optionally from a .dwt template path)."""
        if template and os.path.exists(template):
            self._doc = self._acad.Documents.Open(template)
        else:
            try:
                self._doc = self._acad.Documents.Add()
            except Exception as e:
                # Fallback to ActiveDocument if .Add() fails (common with Late Binding in pywin32)
                self.use_active_drawing()
                return

        self._acad.ActiveDocument = self._doc
        self._mspace = self._doc.ModelSpace
        print_ok("New drawing created")

    def use_active_drawing(self) -> None:
        """Attach to the currently active AutoCAD document."""
        self._doc    = self._acad.ActiveDocument
        self._mspace = self._doc.ModelSpace
        print_ok(f"Using active document: {self._doc.Name}")

    # ── Layer management ─────────────────────────────────────────

    def setup_layers(self, layers_config: Dict[str, Dict]) -> None:
        """Create / configure layers from a config dictionary."""
        for name, props in layers_config.items():
            try:
                layer = self._doc.Layers.Item(name)
            except Exception:
                layer = self._doc.Layers.Add(name)
            layer.Color = props.get("color", 7)
            try:
                lt = props.get("linetype", "Continuous")
                if lt != "Continuous":
                    self._doc.Linetypes.Load(lt, "acad.lin")
                layer.Linetype = lt
            except Exception:
                pass
        print_ok(f"Layers configured: {', '.join(layers_config.keys())}")

    def set_layer(self, layer_name: str) -> None:
        """Set the current active layer."""
        self._doc.ActiveLayer = self._doc.Layers.Item(layer_name)

    # ── Drawing primitives ───────────────────────────────────────

    def draw_lwpolyline(
        self,
        flat_points: List[float],
        layer:  str  = "0",
        closed: bool = False,
        width:  float = 0.0,
    ) -> Any:
        """
        Draw a 2-D LightWeightPolyline.

        Parameters
        ----------
        flat_points : [x1,y1, x2,y2, … , xN,yN]
        layer       : layer name (must already exist in the drawing)
        closed      : whether to close the polyline
        width       : constant width in drawing units (0 = hairline)

        Returns
        -------
        AcadLWPolyline COM object
        """
        if len(flat_points) < 4:
            raise ValueError("Need at least 2 points (4 values) for a polyline.")

        var  = _make_variant(flat_points)
        pline = self._mspace.AddLightWeightPolyline(var)
        pline.Layer  = layer
        pline.Closed = closed
        if width > 0:
            pline.ConstantWidth = width
        return pline

    def draw_text(
        self,
        text:   str,
        x:      float,
        y:      float,
        height: float = 3.0,
        layer:  str   = "LABELS",
    ) -> Any:
        """
        Add a single-line text entity.

        Returns
        -------
        AcadText COM object
        """
        pt  = _make_point_variant(x, y)
        txt = self._mspace.AddText(text, pt, float(height))
        txt.Layer = layer
        return txt

    def draw_circle(
        self,
        cx: float, cy: float,
        radius: float,
        layer:  str = "MARKERS",
    ) -> Any:
        """Draw a circle (used for terminal markers)."""
        center = _make_point_variant(cx, cy)
        circ   = self._mspace.AddCircle(center, float(radius))
        circ.Layer = layer
        return circ

    # ── View / units ─────────────────────────────────────────────

    def set_units(self, insunits: int = 6) -> None:
        """
        Set drawing units variable.
        6 = micrometers (INSUNITS system variable).
        """
        self._doc.SetVariable("INSUNITS", insunits)

    def zoom_extents(self) -> None:
        """Zoom to fit all entities."""
        self._acad.ZoomExtents()

    def regen(self) -> None:
        """Regenerate the drawing view."""
        self._doc.Regen(True)

    # ── Saving ───────────────────────────────────────────────────

    def save(self, filepath: str, fmt: str = "dwg") -> None:
        """
        Save the active drawing.

        Parameters
        ----------
        filepath : full absolute path, e.g. r"D:\\AUTOCAD_ENGINE\\saves\\heater.dwg"
        fmt      : "dwg" (default) or "dxf"

        Notes
        -----
        AcSaveAsType enum used:
          0  → native / current DWG format  (acNative)
          4  → DXF R2010                    (acR2010_dxf)
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        fmt = fmt.lower().strip(".")
        if fmt == "dwg":
            # acNative = 1 in most AutoCAD versions; 0 also works as "current format"
            try:
                self._doc.SaveAs(filepath, 1)          # acNative
            except Exception:
                self._doc.SaveAs(filepath)             # fallback: no format arg
        elif fmt == "dxf":
            try:
                self._doc.SaveAs(filepath, 4)          # DXF R2010
            except Exception:
                # If format code fails, save as DWG then rename – last resort
                tmp = filepath.replace(".dxf", "_tmp.dwg")
                self._doc.SaveAs(tmp, 1)
                print_err("DXF save via COM failed; file saved as DWG instead.")
                print_info(f"  Saved to: {tmp}")
                return
        else:
            raise ValueError(f"Unsupported format: '{fmt}'. Use 'dwg' or 'dxf'.")

        print_ok(f"Saved → {filepath}")
