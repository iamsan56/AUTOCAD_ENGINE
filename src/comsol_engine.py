"""
src/comsol_engine.py — COMSOL Multiphysics Automation Engine

Wraps the COMSOL Java API via the `mph` Python package.
Allows loading a base template, injecting DXF geometries, and running studies.
"""

import os
import sys

try:
    import mph
except ImportError:
    mph = None

from src.utils import print_ok, print_info, print_err


class ComsolEngine:
    """
    Live COMSOL Multiphysics bridge via mph.
    
    Usage:
    with ComsolEngine() as engine:
        engine.load_template("base_template.mph")
        engine.import_geometry("path.dxf")
        engine.solve()
        engine.save("output.mph")
    """
    def __init__(self) -> None:
        if mph is None:
            raise ImportError("The 'mph' package is required. Run: pip install mph")
        self.client = None
        self.model = None

    def __enter__(self) -> "ComsolEngine":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

    def connect(self) -> None:
        """Start the COMSOL client session."""
        print_info("Starting COMSOL Multiphysics client (this may take a moment)...")
        # Start client, suppressing heavy logging if possible
        self.client = mph.start()
        print_ok("Connected to COMSOL Server via JPype.")

    def load_template(self, template_path: str) -> None:
        """Load a base .mph template file."""
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")
        print_info(f"Loading COMSOL template: {template_path} ...")
        self.model = self.client.load(template_path)
        print_ok(f"Loaded model: {self.model.name()}")

    def import_geometry(self, dxf_path: str, component_name: str = "comp1", geom_name: str = "geom1") -> None:
        """
        Inject a DXF file into the geometry node and build it.
        Uses direct Java API fallback if the MPh wrapper doesn't map 'Import'.
        """
        print_info(f"Importing DXF into {component_name}/{geom_name} ...")
        try:
            java_model = self.model.java
            
            # Check if geometry node exists
            if not java_model.geom().has(geom_name):
                # Fallback to the first geometry node available if 'geom1' isn't used
                geom_tags = list(java_model.geom().tags())
                if not geom_tags:
                    raise RuntimeError("No geometry node found in the template.")
                geom_name = geom_tags[0]
                print_info(f"Using geometry node: {geom_name}")

            geom = java_model.geom(geom_name)
            
            # Create an Import node
            imp_tag = geom.feature().uniquetag("imp")
            imp = geom.feature().create(imp_tag, "Import")
            imp.set("filename", dxf_path)
            
            # Force COMSOL to interpret closed curves/regions as Solid faces
            try:
                imp.set("type", "solid")
            except Exception:
                pass # Depending on COMSOL version, property might be seltype or similar, but type=solid is standard for DXF import

            # Build geometry
            geom.run()
            print_ok(f"Geometry imported and built successfully under node '{imp_tag}'.")
        except Exception as e:
            print_err(f"Failed to import geometry: {e}")
            raise

    def solve(self, study_name: str = "std1") -> None:
        """Mesh the geometry and run the study."""
        print_info("Generating mesh...")
        try:
            self.model.mesh()
            print_ok("Mesh generated.")
        except Exception as e:
            print_err(f"Meshing failed (ensure template has a mesh node): {e}")
            raise
            
        print_info("Computing study (this may take a while)...")
        try:
            java_model = self.model.java
            
            # Verify study exists
            if not java_model.study().has(study_name):
                study_tags = list(java_model.study().tags())
                if not study_tags:
                    raise RuntimeError("No study node found in the template.")
                study_name = study_tags[0]
                print_info(f"Using study node: {study_name}")
                
            self.model.solve(study_name)
            print_ok("Study computation completed successfully.")
        except Exception as e:
            print_err(f"Study computation failed: {e}")
            raise

    def save(self, filepath: str) -> None:
        """Save the updated .mph file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.model.save(filepath)
        print_ok(f"Saved simulated COMSOL model to: {filepath}")

    def disconnect(self) -> None:
        """Disconnect and clear memory."""
        self.model = None
        if self.client:
            # mph handles JVM shutdown on exit, but we can clear models
            self.client.clear()
        print_ok("COMSOL resources released.")
