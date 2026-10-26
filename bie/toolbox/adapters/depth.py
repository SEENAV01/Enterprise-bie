"""A depth map for one picture, so BIE's code can move a still in 2.5D (Task 046 one-shot test, Route 2, 26 October 2026).

Depth Anything V2 Small (Apache-2.0; the Base and Large models are CC BY-NC and never used) through ONNX Runtime (MIT),
from the onnx-community export pinned by revision and checked by SHA-256; the 99 MB model is fetched once into the asset
cache (``BIE_ASSET_CACHE/depth``), never into git. ``estimate`` writes a 16-bit greyscale PNG the size of the picture:
white is near, black is far (the model's relative inverse depth, stretched to the full range), and returns its numbers.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .base import need

MODEL = {"name": "Depth Anything V2 Small (onnx-community export)", "licence": "Apache-2.0",
         "source": "https://huggingface.co/depth-anything/Depth-Anything-V2-Small-hf",
         "revision": "4472b7362082ad9968fee890ca0f1e5aca36b93d",
         "url": "https://huggingface.co/onnx-community/depth-anything-v2-small/resolve/4472b7362082ad9968fee890ca0f1e5aca36b93d/onnx/model.onnx",
         "sha256": "afb6a5c28f3b6bf1618c6e43f02073ef9dfdc70e937502d51603e57b0a1df10c", "bytes": 99060839,
         "credit": "Depth Anything V2 (Yang et al., 2024), Small model, Apache-2.0"}
SIDE = 518                      # the model's input: a multiple of its 14-pixel patches
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)


def model_path(cache: Path | None = None, *, opener=None) -> Path:
    from ..sources import cache_dir, fetch
    folder = Path(cache or cache_dir()) / "depth"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"depth-anything-v2-small-{MODEL['revision'][:8]}.onnx"
    if path.exists() and path.stat().st_size == MODEL["bytes"]:
        return path
    data = fetch(MODEL["url"], opener=opener, timeout=600.0, max_bytes=MODEL["bytes"] + 1024)
    digest = hashlib.sha256(data).hexdigest()
    if digest != MODEL["sha256"]:
        raise RuntimeError(f"depth model: SHA-256 {digest} is not the pinned {MODEL['sha256']}")
    part = path.with_suffix(".part")
    part.write_bytes(data)
    part.replace(path)
    return path


def prepare(image, side: int = SIDE):
    """The picture as the model's input tensor (1, 3, side, side), ImageNet-normalised."""
    np = need("numpy")
    rgb = image.convert("RGB").resize((side, side), resample=3)          # bicubic
    x = np.asarray(rgb, dtype=np.float32) / 255.0
    x = (x - np.array(MEAN, dtype=np.float32)) / np.array(STD, dtype=np.float32)
    return x.transpose(2, 0, 1)[None].astype(np.float32)


def to_png16(depth, size) -> "Image":
    """The model's output stretched to 0..65535 (near = white) at the picture's size."""
    np = need("numpy")
    from PIL import Image
    d = np.asarray(depth, dtype=np.float32).squeeze()
    lo, hi = float(np.percentile(d, 0.5)), float(np.percentile(d, 99.5))
    d = np.clip((d - lo) / max(1e-6, hi - lo), 0.0, 1.0)
    img = Image.fromarray((d * 65535).astype(np.uint16))
    return img.resize(size, resample=2)                                  # bilinear


def estimate(picture: str | Path, out_png: str | Path, *, cache: Path | None = None, session=None) -> dict:
    from PIL import Image
    image = Image.open(picture)
    if session is None:
        ort = need("onnxruntime")
        session = ort.InferenceSession(str(model_path(cache)), providers=["CPUExecutionProvider"])
    name = session.get_inputs()[0].name
    depth = session.run(None, {name: prepare(image)})[0]
    png = to_png16(depth, image.size)
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    png.save(out_png)
    np = need("numpy")
    arr = np.asarray(png, dtype=np.float32) / 65535.0
    return {"model": MODEL["name"], "licence": MODEL["licence"], "revision": MODEL["revision"], "size": list(image.size),
            "near_share": round(float((arr > 0.66).mean()), 3), "far_share": round(float((arr < 0.15).mean()), 3), "out": str(out_png)}


def layout_anchors(depth_png: str | Path, labels: list, member: str, *, edge_u: float = 0.66, focus_u: float = 0.48) -> dict:
    """Where BIE's labels point on a still, found in its depth map (the still carries no text, VG-02): the far edge of the
    layer is the sharpest step from far to near down one column (the ``boundary`` label); the member's own label points
    at a cell between that edge and the bottom. Returns {"anchors_uv": {label: [u, v]}, "focus_uv": [u, v], "edge_v": v};
    a label it cannot place is left out."""
    np = need("numpy")
    from PIL import Image
    d = np.asarray(Image.open(depth_png), dtype=np.float32)
    d = d / (65535.0 if d.max() > 255 else 255.0)
    h, w = d.shape[:2]
    x = int(round(edge_u * (w - 1)))
    col = d[:, max(0, x - 6):x + 7].mean(axis=1)
    col = np.convolve(col, np.ones(9) / 9, mode="same")
    top, bottom = int(0.04 * h), int(0.75 * h)
    step = np.diff(col)[top:bottom]
    edge_v = float(top + int(np.argmax(step)) + 4) / h
    focus_v = edge_v + 0.45 * (1 - edge_v)
    # snap to the nearest bump (a nucleus dome stands out of its cell): the depth minus its local mean, highest within reach
    k = max(3, int(0.03 * h)) | 1
    pad = np.pad(d, k, mode="edge")
    c = pad.cumsum(0).cumsum(1)
    mean = (c[2 * k:, 2 * k:] - c[:-2 * k, 2 * k:] - c[2 * k:, :-2 * k] + c[:-2 * k, :-2 * k]) / (2 * k) ** 2
    bump = d - mean[:h, :w]
    y0, y1 = int((focus_v - 0.07) * h), int((focus_v + 0.07) * h)
    x0, x1 = int((focus_u - 0.05) * w), int((focus_u + 0.05) * w)
    window = bump[max(0, y0):y1, max(0, x0):x1]
    if window.size:
        yy, xx = np.unravel_index(int(np.argmax(window)), window.shape)
        focus_u, focus_v = (max(0, x0) + xx) / w, (max(0, y0) + yy) / h
    focus_u, focus_v = round(float(focus_u), 3), round(float(focus_v), 3)
    anchors = {}
    for label in labels:
        low = label.lower()
        if low == member.lower() or low in member.lower():
            anchors[label] = [focus_u, focus_v]
        elif any(word in low for word in ("boundary", "edge", "layer", "barrier")):
            anchors[label] = [edge_u, round(min(0.95, edge_v + 0.015), 3)]
    return {"anchors_uv": anchors, "focus_uv": [focus_u, focus_v], "edge_v": round(edge_v, 3)}
