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
}


class Unavailable(RuntimeError):
    """A library the adapter needs is not installed here."""


def need(tool_id: str):
    module, _, group = PYTHON_TOOLS[tool_id]
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise Unavailable(f"{tool_id} is not installed: pip install -e '.[{group}]' ({exc})") from None


def installed_version(tool_id: str) -> str | None:
    _, dist, _ = PYTHON_TOOLS[tool_id]
    try:
        return importlib.metadata.version(dist)
    except importlib.metadata.PackageNotFoundError:
        return None


def clean(value, digits: int = 4):
    """Round floats and turn NaN or infinity into None, so the data is valid JSON for the web blocks."""
    if isinstance(value, float):
        return None if not math.isfinite(value) else round(value, digits)
    if isinstance(value, dict):
        return {k: clean(v, digits) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v, digits) for v in value]
    if hasattr(value, "tolist"):
        return clean(value.tolist(), digits)
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        return clean(value.item(), digits)
    return value
