# AutoCAD Engine 🔧
> **Python → AutoCAD COM automation** — opens AutoCAD, draws parametric designs as a macro, and saves `.dwg` / `.dxf` to the `saves\` folder.

---

## Prerequisites

| Requirement | Minimum version | Notes |
|-------------|----------------|-------|
| **Python** | 3.10+ | [python.org/downloads](https://www.python.org/downloads/) |
| **AutoCAD** | Any modern version | Must be installed on this machine |
| **Windows** | 10 / 11 | COM interface is Windows-only |

---

## 1 — Clone / Open the Project

Open **PowerShell** and navigate to the project folder:

```powershell
cd D:\AUTOCAD_ENGINE
```

---

## 2 — Create a Virtual Environment

```powershell
# Create the venv (only needed once)
python -m venv venv
```

You will see a new `venv\` folder appear inside `D:\AUTOCAD_ENGINE\`.

---

## 3 — Activate the Virtual Environment

Run this **every time** you open a new terminal before running the project:

```powershell
venv\Scripts\activate
```

Your prompt will change to show `(venv)` at the start:

```
(venv) PS D:\AUTOCAD_ENGINE>
```

> **To deactivate** when you are done:
> ```powershell
> deactivate
> ```

---

## 4 — Install Dependencies

With the venv active, install all required packages:

```powershell
pip install -r requirements.txt
```

Expected output:
```
Collecting pywin32>=306
  Downloading pywin32-306-cp311-cp311-win_amd64.whl ...
Successfully installed pywin32-306
```

> After installing `pywin32`, run the post-install script once:
> ```powershell
> python venv\Scripts\pywin32_postinstall.py -install
> ```
> This registers the COM components so AutoCAD can be found.

---

## 5 — Verify Installation

```powershell
python -c "import win32com.client; print('pywin32 OK ✅')"
```

You should see:
```
pywin32 OK ✅
```

---

## 6 — Run the Engine

Simply run:

```powershell
python main.py
```

You will see an **interactive menu** — no need to type any flags:

```
  ╔═══════════════════════════════════════════════════╗
  ║           A U T O C A D   E N G I N E            ║
  ║         Python → COM Macro Automation            ║
  ╚═══════════════════════════════════════════════════╝

  ┌─────────────────────────────────────────────────────┐
  │            Which design do you want?                │
  └─────────────────────────────────────────────────────┘

    [1]  Mirrored Wavy Microheater
         Serpentine microheater with sinusoidal wave pattern…

    [2]  Hexagonal Spiral Microheater
         8 concentric flat-top hexagonal rings (100 µm → 30 µm)…

  Enter number: 2

  ✅  Selected: Hexagonal Spiral Microheater

  ┌─────────────────────────────────────────────────────┐
  │              Which format to save?                  │
  └─────────────────────────────────────────────────────┘

    [1]  DWG  — AutoCAD native format
    [2]  DXF  — text-based, universal format
    [3]  Both DWG and DXF

  Enter number [1]: 3

  ✅  Format: Both DWG and DXF
```

AutoCAD opens automatically, draws the design (white lines, no text), and saves to `saves\`.

---

## Command Reference

| Command | What it does |
|---------|-------------|
| `python main.py` | **Interactive menu** — pick design & format |
| `python main.py --design microheater --format dwg` | Non-interactive, microheater → DWG |
| `python main.py --design hex_spiral_heater --format both` | Non-interactive, hex spiral → DWG+DXF |
| `python main.py --list` | Print all registered designs |
| `python main.py --help` | Show all CLI options |
| `python designs\microheater.py` | Geometry self-test, no AutoCAD needed |
| `python designs\hex_spiral_heater.py` | Hex spiral self-test, no AutoCAD needed |

---

## What Happens When You Run

```
┌──────────────────────────────────────────────────────┐
│  AutoCAD Engine  →  Mirrored Wavy Microheater        │
└──────────────────────────────────────────────────────┘
  ℹ️   Generating geometry …
  ✅  Path generated: 1027 vertices
  ✅  Connected to existing AutoCAD instance   ← or "Launched AutoCAD"
  ✅  New drawing created
  ✅  Layers configured: MICROHEATER, LABELS, MARKERS
  ✅  Microheater path drawn on layer 'MICROHEATER'
  ✅  Terminal markers added: ['IN', 'OUT']
  ✅  Saved → D:\AUTOCAD_ENGINE\saves\microheater_2026-06-24_153045.dwg

┌──────────┐
│  Done    │
└──────────┘
  ✅  Output  → D:\AUTOCAD_ENGINE\saves\microheater_2026-06-24_153045.dwg
  ℹ️   Saves folder: D:\AUTOCAD_ENGINE\saves
```

AutoCAD **opens automatically** if it is not already running.  
The output file is saved with a timestamp so previous files are never overwritten.

---

## Project Structure

```
D:\AUTOCAD_ENGINE\
│
├── main.py              ← ▶  Entry point — run this
├── config.py            ← ⚙   Paths, layer defs, design parameters
├── requirements.txt     ← 📦  Python dependencies
├── README.md            ← 📖  This file
│
├── src\
│   ├── __init__.py
│   ├── cad_engine.py    ← AutoCAD COM bridge  (pywin32 / win32com)
│   ├── shapes.py        ← wavy_pts(), arc_pts() geometry generators
│   ├── layers.py        ← Layer creation helpers
│   └── utils.py         ← File naming, console printing
│
├── designs\
│   ├── __init__.py
│   └── microheater.py   ← Mirrored Wavy Microheater design
│
├── saves\               ← 💾  All .dwg / .dxf output files land here
│   └── microheater_<timestamp>.dwg
│
└── venv\                ← 🐍  Virtual environment (created by you in Step 2)
```

---

## Design: Mirrored Wavy Microheater

| Property | Value |
|----------|-------|
| IN terminal | (−40, 0) µm |
| OUT terminal | (0, 0) µm |
| Wave amplitude | 5 µm |
| Wave period | 10 µm |
| Total path segments | 9 |
| Overall width | 80 µm |
| Overall height | 82 µm |

**Path topology:**
```
IN(-40,0) ──► wavy UP  (outer-left)  ──► wavy RIGHT (top)
          ──► wavy DOWN (outer-right) ──► U-turn (bottom-right)
          ──► wavy UP  (inner-right)  ──► U-turn (top-inner)
          ──► wavy DOWN (inner-left)  ──► U-turn (bottom-center)
          ──► short DOWN              ──► OUT(0,0)
```

---

## Command Reference

| Command | What it does |
|---------|-------------|
| `python main.py` | Draw **microheater**, save as `.dwg` |
| `python main.py --design hex_spiral_heater` | Draw **hexagonal spiral**, save as `.dwg` |
| `python main.py --format dxf` | Save as `.dxf` |
| `python main.py --format both` | Save as `.dwg` **and** `.dxf` |
| `python main.py --design microheater --format both` | Microheater, both formats |
| `python main.py --design hex_spiral_heater --format both` | Hex spiral, both formats |
| `python main.py --list` | Print all registered designs |
| `python main.py --help` | Show all CLI options |
| `python designs\microheater.py` | Geometry self-test, no AutoCAD needed |
| `python designs\hex_spiral_heater.py` | Hex spiral self-test, no AutoCAD needed |

---

## Adding a New Design

1. Create `designs\my_design.py` implementing:
   ```python
   def build_path(params=None) -> list[float]: ...   # returns [x,y,x,y,…]
   def get_terminal_markers() -> list[dict]: ...      # optional
   DESIGN_META = {"name": "my_design", "title": "…", "layer": "MICROHEATER", "description": "…"}
   ```

2. Register in `main.py`:
   ```python
   DESIGN_REGISTRY["my_design"] = "designs.my_design"
   ```

3. Run:
   ```powershell
   python main.py --design my_design --format both
   ```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: win32com` | Run `pip install -r requirements.txt` inside the venv |
| `(venv)` not showing in prompt | Run `venv\Scripts\activate` first |
| AutoCAD does not open | Check AutoCAD is installed; try opening it manually first |
| `SaveAs` permission error | Make sure `saves\` folder exists and is not read-only |
| COM error / frozen | Restart AutoCAD, then re-run `python main.py` |
| `pywin32_postinstall` error | Run PowerShell **as Administrator** and retry the post-install step |
