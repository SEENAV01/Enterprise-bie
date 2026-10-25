"""Shared helpers for the toolbox adapters: import a library or say how to install it, and read installed versions."""
from __future__ import annotations

import importlib
import importlib.metadata
import math

# tool id → (Python module, distribution on PyPI, install group in pyproject.toml)
PYTHON_TOOLS = {
    "numpy": ("numpy", "numpy", "toolbox-core"),
    "scipy": ("scipy", "scipy", "toolbox-core"),
    "sympy": ("sympy", "sympy", "toolbox-core"),
    "networkx": ("networkx", "networkx", "toolbox-core"),
    "statsmodels": ("statsmodels", "statsmodels", "toolbox-stats"),
    "biopython": ("Bio", "biopython", "toolbox-bio"),
    "neurokit2": ("neurokit2", "neurokit2", "toolbox-bio"),
    "rdkit": ("rdkit", "rdkit", "toolbox-chem"),
    "cantera": ("cantera", "cantera", "toolbox-chem"),
    "trimesh": ("trimesh", "trimesh", "toolbox-mesh"),
    "manim": ("manim", "manim", "toolbox-manim"),
    "blender": ("bpy", "bpy", "toolbox-blender"),
    # batch 2: electrical, mechanical and civil, earth, astronomy, aerospace
    "scipy-signal": ("scipy.signal", "scipy", "toolbox-core"),
    "sympy-physics": ("sympy.physics.continuum_mechanics", "sympy", "toolbox-core"),
    "schemdraw": ("schemdraw", "schemdraw", "toolbox-electrical"),
    "lcapy": ("lcapy", "lcapy", "toolbox-electrical"),
    "python-control": ("control", "control", "toolbox-electrical"),
    "pynite": ("Pynite", "PyNiteFEA", "toolbox-mech"),
    "coolprop": ("CoolProp", "CoolProp", "toolbox-mech"),
    "cadquery": ("cadquery", "cadquery", "toolbox-mech"),
    "scikit-fem": ("skfem", "scikit-fem", "toolbox-mech"),
    "obspy": ("obspy", "obspy", "toolbox-earth"),
    "pygmt": ("pygmt", "pygmt", "toolbox-earth"),
    "pygplates": ("pygplates", "pygplates", "toolbox-earth"),
    "astropy": ("astropy", "astropy", "toolbox-astro"),
    "skyfield": ("skyfield", "skyfield", "toolbox-astro"),
    "aerosandbox": ("aerosandbox", "aerosandbox", "toolbox-aero"),
    "jsbsim": ("jsbsim", "jsbsim", "toolbox-aero"),
    # batch 3: maps, law data, behaviour, languages
    "shapely": ("shapely", "shapely", "toolbox-maps"),
    "pyarrow": ("pyarrow", "pyarrow", "toolbox-law"),
    "psychopy": ("psychopy.data", "psychopy", "toolbox-behaviour"),
    "indic-nlp": ("indicnlp", "indic-nlp-library", "toolbox-language"),
    "indic-transliteration": ("indic_transliteration.sanscript", "indic-transliteration", "toolbox-language"),
}

# Installed by the toolbox lane with pip --no-deps --ignore-requires-python (a pyproject extra cannot say that): PsychoPy's
# own pins need Python < 3.13 and a desktop stack; BIE uses only psychopy.data, whose two small needs are in its extra.
NO_DEPS = {"psychopy": "2026.2.4"}
INSTALL_HINTS = {tid: f"pip install -e '.[{PYTHON_TOOLS[tid][2]}]' && pip install --no-deps --ignore-requires-python {PYTHON_TOOLS[tid][1]}=={v}"
                 for tid, v in NO_DEPS.items()}

# tool id → (program on PATH, the apt package that installs it): programs BIE runs, not Python libraries
PROGRAMS = {"ngspice": ("ngspice", "ngspice"), "gmt": ("gmt", "gmt libgmt-dev gmt-dcw gmt-gshhg-low ghostscript")}


class Unavailable(RuntimeError):
    """A library the adapter needs is not installed here."""


def need(tool_id: str):
    module, _, group = PYTHON_TOOLS[tool_id]
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        hint = INSTALL_HINTS.get(tool_id) or f"pip install -e '.[{group}]'"
        raise Unavailable(f"{tool_id} is not installed: {hint} ({exc})") from None


def need_program(tool_id: str) -> str:
    """The path of a program BIE runs (ngspice, gmt), or Unavailable with the apt line that installs it."""
    import shutil
    program, apt = PROGRAMS[tool_id]
    found = shutil.which(program)
    if not found:
        raise Unavailable(f"{tool_id} is not installed: sudo apt-get install {apt}")
    return found


def program_version(tool_id: str) -> str | None:
    import re
    import subprocess
    program, _ = PROGRAMS[tool_id]
    try:
        done = subprocess.run([program, "--version"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    found = re.search(r"(\d+(?:\.\d+)*)", (done.stdout or "") + (done.stderr or ""))
    return found.group(1) if found else None


def installed_version(tool_id: str) -> str | None:
    if tool_id in PROGRAMS:
        return program_version(tool_id)
    _, dist, _ = PYTHON_TOOLS[tool_id]
    try:
        return importlib.metadata.version(dist)
    except importlib.metadata.PackageNotFoundError:
        return None


def clean(value, digits: int = 4):
    """Round floats and turn NaN or infinity into None, so the data is valid JSON for the web blocks."""
    if isinstance(value, float):
        return None if not math.isfinite(value) else round(float(value), digits)
    if isinstance(value, dict):
        return {k: clean(v, digits) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v, digits) for v in value]
    if hasattr(value, "tolist"):
        return clean(value.tolist(), digits)
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        return clean(value.item(), digits)
    return value
