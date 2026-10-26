"""LOOK-01: the look check (Task 046 one-shot test, after Navin rejected Part B on 26 October 2026).

The Part B frame checks measured presence (a caption band, a label box, accent pixels, a dark frame, motion) and passed
frames that looked nothing like the benchmark (SEEKH_LOG entry 13). LOOK-01 asks a reviewer with image input to compare
our frames with the benchmark's frames on what the eye sees: organic shape, translucency, lighting and depth, detail,
scientific correctness and the overall class of the picture, each 1 to 10 with its reason. The score is advice only;
Navin's eye decides. The benchmark's frames never leave the machine that holds them (they are not ours to publish): a
request names a private reference set kept on that machine, or, without it, a written description of the benchmark's
look, and the result says which one was used.
"""
from __future__ import annotations

RULE = "LOOK-01"
VERSION = "2026-10-26.1"
AXES = (
    ("organic_shape", "Organic shape: irregular, interlocking cell outlines, soft domed tops, a nucleus bulge; not geometric prisms."),
    ("translucency", "Translucency: light passes into and through the cells (subsurface scattering); nuclei read as denser bodies inside."),
    ("lighting_depth", "Lighting and depth: a key light and a rim light, soft haze, depth of field, planes separated in depth."),
    ("detail", "Detail: fine surface texture and membranes, crisp at the focus, nothing plastic or flat-shaded."),
    ("science", "Scientific correctness for the shot: one single thin layer of flat cells, a nucleus per cell, a basement membrane below."),
    ("same_class", "Overall: would a viewer place this in the same class of animation as the reference frames?"),
)
SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["scores", "reasons", "biggest_gap", "verdict"],
    "properties": {
        "scores": {"type": "object", "additionalProperties": False, "required": [a for a, _ in AXES],
                   "properties": {a: {"type": "integer", "minimum": 1, "maximum": 10} for a, _ in AXES}},
        "reasons": {"type": "object", "additionalProperties": False, "required": [a for a, _ in AXES],
                    "properties": {a: {"type": "string", "minLength": 10} for a, _ in AXES}},
        "biggest_gap": {"type": "string", "minLength": 10},
        "verdict": {"type": "string", "enum": ["same class", "close", "far"]},
    },
}
SYSTEM = ("You are BIE's look reviewer (rule LOOK-01). You compare frames of a science animation BIE rendered with reference "
          "frames of the animation BIE is measured against. Judge only what the eye sees in the images; text, labels and "
          "captions drawn on frames are BIE's code overlays and are not part of the look. Be strict and honest: a 10 means "
          "indistinguishable in quality from the reference, a 5 means clearly a step below, a 1 means a different class "
          "entirely. Give one short concrete reason per score. Reply with one JSON object that matches the schema.")


def task_text(shot: dict, *, reference: str, route: str, frames: int, references: int, description: str = "") -> str:
    axes = "\n".join(f"- {name}: {text}" for name, text in AXES)
    ref = (f"The first {references} images are the REFERENCE frames (the benchmark). The next {frames} images are BIE's frames "
           f"from {route}." if reference == "frames" else
           f"No reference image is attached; the benchmark's look is described in words here: {description}\n"
           f"The {frames} images are BIE's frames from {route}.")
    return (f"Shot: {shot.get('sentence', '')}\nWhat it must show: {shot.get('must_show', '')}\n\n{ref}\n\n"
            f"Score BIE's frames 1 to 10 on each axis, against the reference:\n{axes}\n\n"
            "Then name the biggest gap in one sentence and give the verdict: same class, close or far.")


def messages(shot: dict, route: str, frames: list, references: list, description: str = "") -> tuple:
    """BIE messages for one route: ``frames`` and ``references`` are [(media_type, base64)]."""
    parts = [{"type": "text", "text": task_text(shot, reference="frames" if references else "description", route=route,
                                                frames=len(frames), references=len(references), description=description)}]
    for label, images in (("REFERENCE", references), ("BIE", frames)):
        for number, (media, data) in enumerate(images, 1):
            parts.append({"type": "text", "text": f"{label} frame {number}:"})
            parts.append({"type": "image", "media_type": media, "data": data})
    return ({"role": "system", "content": SYSTEM}, {"role": "user", "content": parts})


def problems(value: dict) -> list:
    """Content checks beyond the schema: a reason per axis that is more than a label."""
    out = []
    for name, _ in AXES:
        reason = str((value.get("reasons") or {}).get(name, ""))
        if len(reason.split()) < 3:
            out.append(f"{name}: give a concrete reason of a few words")
    return out


def summary(results: dict) -> dict:
    """{route: {axis: score}, ...} → the rows of the rule table: mean per route and the overall."""
    rows = {}
    for route, value in results.items():
        scores = (value or {}).get("scores") or {}
        if scores:
            rows[route] = {"mean": round(sum(scores.values()) / len(scores), 2), "same_class": scores.get("same_class"),
                           "verdict": value.get("verdict")}
    return rows
