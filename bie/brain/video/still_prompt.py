"""Route 2 of the Task 046 one-shot test: BIE writes the prompt for an AI-made still from a shot (26 October 2026).

The picture model makes only the photoreal plate. Everything a learner reads (labels, caption) is drawn by BIE's code on
top (VG-02), so every prompt forbids letters of any kind. The layout comes from the presets of Route 1's Blender recipe
(``bie/toolbox/blender/epithelium_studio.json``): the camera's angle, what fills the frame, what sits behind out of
focus. So the two routes can be judged side by side, and BIE's labels land on the same places. The science comes from a
member sheet: what an expert would check, and what must not appear. Output: a ``bie.image-prompts/1`` file for the VM's
image job (``tools/vm_image.py``, Codex's built-in image_gen through the ChatGPT plan).
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

SCHEMA = "bie.image-prompts/1"
VERSION = "2026-10-26.1"
PRESETS = Path(__file__).resolve().parents[2] / "toolbox" / "blender" / "epithelium_studio.json"
MAX_IMAGES = 4
NO_TEXT = ("Absolutely no text of any kind: no letters, words, numbers, labels, arrows, captions, watermark, logo, signature, "
           "scale bar, border or user interface anywhere in the image.")
STYLE = ("Photorealistic scientific 3D render in the style of a high-end medical animation still: macro photography look, "
         "subsurface scattering, translucent living tissue, soft wet sheen, fine surface texture, cinematic lighting.")

MEMBERS = {
    "simple squamous": {
        "science": ("A single layer of very thin, flat, scale-like simple squamous epithelial cells, fitted together like "
                    "irregular paving stones. Every cell is much wider than it is thick. Each cell outline is irregular, "
                    "with wavy, interlocking borders and a narrow dark groove between neighbouring cells. Each cell has "
                    "exactly one oval nucleus near its centre that makes a small rounded bulge in the flat top surface; "
                    "the nuclei are a darker mauve than the cytoplasm, and faint darker granules show inside the "
                    "cytoplasm. The layer rests on a thin basement membrane."),
        "context": ("Just behind and below the far edge of the layer, softly out of focus, a capillary carrying red blood "
                    "cells (biconcave discs), very close to the thin layer: the short path for exchange."),
        # the particles that cross the layer are drawn by BIE's code so they move (B-04); frozen ones in the still would not
        "exchange": "Keep the space above the layer clear: no floating spheres, bubbles, droplets or particles.",
        "colour": "Warm pink-mauve tissue lit from within, darker mauve nuclei, a deep navy-black background.",
        "must_not": ("Do not show cilia, microvilli, stacked layers, tall column-shaped or cube-shaped cells, cells with two "
                     "or more nuclei, a regular hexagonal honeycomb, cartoon outlines or flat illustration shading."),
    },
}
VARIANTS = (
    ("a", ""),
    ("b", "Slightly stronger warm glow in the centre cell."),
    ("c", "Slightly more pronounced nucleus bulges."),
    ("d", "Slightly more haze toward the far edge."),
)


def presets(path: Path | None = None) -> dict:
    return json.loads(Path(path or PRESETS).read_text(encoding="utf-8"))


def camera_words(camera: dict) -> dict:
    """How the Blender camera sees the sheet, in words a picture model follows: its angle from the horizontal at the start
    of the push-in, and where the far edge of the sheet crosses the frame."""
    (fx, fy, fz), (tx, ty, tz) = camera["from"], camera["target"]
    elevation = math.degrees(math.atan2(fz - tz, math.hypot(tx - fx, ty - fy)))
    return {"elevation_deg": round(elevation, 1),
            "text": (f"The camera looks down at the layer at about {round(elevation / 5) * 5} degrees from the horizontal. "
                     "Wide 16:9 landscape framing: the layer fills the lower four fifths of the frame and runs off the left, "
                     "right and bottom edges; its far edge crosses the upper part of the frame, with darkness above it. "
                     "Shallow depth of field: sharp on the cell in the centre, the nearest cells and everything behind the "
                     "far edge softly blurred.")}


def shot_prompts(shot: dict, *, preset_data: dict | None = None, count: int = MAX_IMAGES) -> dict:
    """The image prompts for one shot: the same layout and science in every prompt, a small variation each."""
    member = (shot.get("member") or "").strip().lower()
    if member not in MEMBERS:
        raise ValueError(f"no member sheet for {member!r}; known: {', '.join(sorted(MEMBERS))}")
    if not 1 <= count <= MAX_IMAGES:
        raise ValueError(f"count must be 1 to {MAX_IMAGES}")
    sheet = MEMBERS[member]
    data = preset_data or presets()
    camera = camera_words(data["defaults"]["camera"])
    light = ("Soft warm key light from the upper left, a cool blue rim light from behind that outlines each nucleus bulge "
             "and cell edge, faint volumetric haze in the distance.")
    base = " ".join([STYLE, sheet["science"], sheet["context"], sheet["exchange"], camera["text"], light, sheet["colour"],
                     sheet["must_not"], NO_TEXT])
    prompts = [{"id": f"{shot['shot_id'].replace('.', '-').lower()}-{key}", "prompt": (base + (" " + extra if extra else "")).strip()}
               for key, extra in VARIANTS[:count]]
    out = {"schema": SCHEMA, "version": VERSION, "shot_id": shot["shot_id"], "member": member,
           "sentence": shot.get("sentence", ""), "layout": {"from": "bie/toolbox/blender/epithelium_studio.json",
                                                           "preset_version": data.get("version"), **camera},
           "labels_by_code": list(shot.get("labels") or []), "prompts": prompts}
    bad = [f"{p['id']}: {problem}" for p in prompts for problem in problems(p["prompt"], shot)]
    if bad:
        raise ValueError("; ".join(bad))
    return out


def problems(prompt: str, shot: dict | None = None) -> list:
    """Code checks on a prompt before it is sent: it forbids text, asks for nothing to be written, stays in size."""
    found = []
    if NO_TEXT not in prompt:
        found.append("the no-text clause is missing")
    if not 40 <= len(prompt) <= 4000 or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", prompt):
        found.append("40 to 4000 characters of plain text")
    if re.search(r"[\"“”'‘’]", prompt):
        found.append("quoted words invite the model to write them")
    for label in (shot or {}).get("labels") or []:
        if re.search(rf"\b(label|labelled|labeled|write|writing|caption)\b[^.]*\b{re.escape(label)}\b", prompt, re.I):
            found.append(f"asks for the label {label!r} in the picture (labels are drawn by code, VG-02)")
    return found
