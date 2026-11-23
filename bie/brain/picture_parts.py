"""A picture's moving parts, cut into layers that the film player moves (Navin, 23 November 2026: "photorealistic cheej
bhi pixels mein hisso mein batte taki parts move kr saken animate ho sake"; after comparing the ATP synthase demos he chose
"routeS: AI tasveer + SAM 2": pressure, rotating, opening and closing like swallowing or gripping, sticking).

The film maker lists the parts of a photo or cutaway that move (``visual.parts``) and what each sentence does to them
(``acts``). After the picture is made, the layout checker looks at it and points at each part (points inside it and a box
around it). Here SAM 2.1 cuts each part from those points: Meta's tiny model (Apache-2.0), ``facebook/sam2.1-hiera-tiny``
on Hugging Face at a fixed revision, read from its safetensors file through transformers on the CPU (about 4 s to load,
2 s per picture, 0.2 s per part). Each cut is cleaned (the pieces the points touch, holes filled) and checked (size, the
points inside it, where it lies against the pointed box); a sound cut becomes a layer: the part's own pixels cropped to
its box with a soft edge, laid back exactly where it was, so the picture looks the same until a part moves. Under the
parts that move away (a jaw that opens, a molecule that slides or leaves, a rotor that turns) the picture gets a plate:
the hole filled from its surroundings (push-pull), so a moving part leaves no ghost.

Only ``Sam2Cutter`` needs torch and transformers; the studio machine's voice environment has both (chatterbox-tts 0.1.7
pins torch 2.6.0 and transformers 5.2.0), so the films section runs ``tools/picture_parts_worker.py`` with that
environment's python. Everything else needs only numpy and Pillow (scipy, when present, cleans the cut)."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageFilter

MODEL = "facebook/sam2.1-hiera-tiny"
REVISION = "de431c4043854a71d8101e17995dfe596bf101a5"        # Hugging Face, Apache-2.0 (read 23 November 2026)
LICENCE = "SAM 2.1 (Meta) Apache-2.0; transformers Apache-2.0; torch BSD-3-Clause"
SIDE = 1024                                                   # SAM 2 sees the picture squashed to 1024 x 1024
MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)
MIN_AREA, MAX_AREA = 0.05, 45.0      # percent of the picture: smaller is a speck, larger is the background
MIN_INSIDE = 0.5                     # share of the pointed points that fall on the cut
MIN_OVERLAP = 0.2                    # the cut's box against the pointed box (intersection over union)
PAD = 1.0                            # percent of margin around a layer's crop, so its soft edge is not clipped


class Sam2Cutter:
    """SAM 2.1 on the CPU: ``look`` at a picture once, then ``mask`` each part from its points and box."""

    def __init__(self, revision: str = REVISION, threads: int | None = None):
        import torch
        from transformers import Sam2Model
        if threads:
            torch.set_num_threads(int(threads))
        self.torch = torch
        self.model = Sam2Model.from_pretrained(MODEL, revision=revision).eval()
        self.embedding = None

    def look(self, image: Image.Image) -> None:
        x = np.asarray(image.convert("RGB").resize((SIDE, SIDE), Image.BILINEAR), dtype=np.float32) / 255.0
        x = (x - MEAN) / STD
        pixels = self.torch.from_numpy(np.ascontiguousarray(x.transpose(2, 0, 1))).unsqueeze(0)
        with self.torch.no_grad():
            self.embedding = self.model.get_image_embeddings(pixels)
        self.size = image.size

    def mask(self, inside: list, outside: list, box: list | None) -> tuple[np.ndarray, float]:
        """The best of SAM's three masks for these points (percent of the picture), as a bool array, and its score."""
        torch, w, h = self.torch, self.size[0], self.size[1]
        points = [[x * SIDE / 100, y * SIDE / 100] for x, y in list(inside) + list(outside)]
        labels = [1] * len(inside) + [0] * len(outside)
        kw = {"input_points": torch.tensor([[points]], dtype=torch.float32),
              "input_labels": torch.tensor([[labels]], dtype=torch.int64)}
        if box:
            kw["input_boxes"] = torch.tensor([[[v * SIDE / 100 for v in box]]], dtype=torch.float32)
        with torch.no_grad():
            out = self.model(image_embeddings=self.embedding, multimask_output=True, **kw)
        scores = out.iou_scores[0, 0].numpy()
        best = int(scores.argmax())
        low = out.pred_masks[0, 0, best][None, None]
        up = torch.nn.functional.interpolate(low, (SIDE, SIDE), mode="bilinear", align_corners=False)
        full = torch.nn.functional.interpolate(up, (h, w), mode="bilinear", align_corners=False)[0, 0]
        return (full > 0).numpy(), float(scores[best])


def _at(mask: np.ndarray, point) -> tuple[int, int]:
    h, w = mask.shape
    return min(h - 1, max(0, int(point[1] * h / 100))), min(w - 1, max(0, int(point[0] * w / 100)))


def clean(mask: np.ndarray, inside: list = (), holes: bool = True) -> np.ndarray:
    """The pieces of the cut that the pointed points touch (the largest piece when none does: a molecule drawn as
    separate balls keeps every ball that was pointed at), with the holes inside them filled (not for a molecule, whose
    gaps between balls are the pocket behind it)."""
    try:
        from scipy import ndimage
    except ImportError:                    # without scipy the cut stays as SAM gave it
        return mask.astype(bool)
    mask = mask.astype(bool)
    labels, n = ndimage.label(mask, structure=np.ones((3, 3), dtype=int))
    if n > 1:
        touched = {int(labels[_at(mask, p)]) for p in inside} - {0}
        if not touched:
            sizes = ndimage.sum(mask, labels, range(1, n + 1))
            touched = {1 + int(np.argmax(sizes))}
        mask = np.isin(labels, sorted(touched))
    return ndimage.binary_fill_holes(mask) if holes else mask


def box_of(mask: np.ndarray) -> list | None:
    """The mask's box in percent of the picture: [x0, y0, x1, y1]."""
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    h, w = mask.shape
    return [round(xs.min() / w * 100, 2), round(ys.min() / h * 100, 2),
            round((xs.max() + 1) / w * 100, 2), round((ys.max() + 1) / h * 100, 2)]


def centre_of(mask: np.ndarray) -> list | None:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    h, w = mask.shape
    return [round(float(xs.mean()) / w * 100, 2), round(float(ys.mean()) / h * 100, 2)]


def overlap(a, b) -> float:
    """Intersection over union of two boxes [x0, y0, x1, y1]."""
    if not a or not b:
        return 0.0
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def check_cut(mask: np.ndarray, inside: list, box: list | None) -> list:
    """Why this cut is not the pointed part ([] when it is): too small, the background, off the points or off the box."""
    area = float(mask.mean()) * 100
    if area < MIN_AREA:
        return [f"the cut is a speck ({area:.2f}% of the picture)"]
    if area > MAX_AREA:
        return [f"the cut covers {area:.0f}% of the picture, so it took the background"]
    out = []
    if inside:
        hit = sum(bool(mask[_at(mask, p)]) for p in inside) / len(inside)
        if hit < MIN_INSIDE:
            out.append(f"only {hit:.0%} of the pointed points are on the cut")
    if box and overlap(box_of(mask), box) < MIN_OVERLAP:
        out.append("the cut lies away from the box the part was pointed in")
    return out


def layer(image: Image.Image, mask: np.ndarray, pad: float = PAD, inner: np.ndarray | None = None) -> tuple[Image.Image, list]:
    """The part's own pixels cropped to its box (plus ``pad`` percent), transparent outside the part with a soft one-pixel
    edge, and that crop's box in percent of the picture. ``inner`` (what the part holds: a molecule in its pocket) is
    painted over from the part's own colours, so the part can move without carrying a copy of what it holds."""
    w, h = image.size
    if inner is not None and (inner & ~mask).any():
        filled = fill(np.asarray(image.convert("RGB")), inner & ~mask, mask)
        image, mask = Image.fromarray(filled, "RGB"), mask | inner
    x0, y0, x1, y1 = box_of(mask)
    x0, y0 = max(0.0, x0 - pad), max(0.0, y0 - pad)
    x1, y1 = min(100.0, x1 + pad), min(100.0, y1 + pad)
    px = (int(x0 * w / 100), int(y0 * h / 100), int(math.ceil(x1 * w / 100)), int(math.ceil(y1 * h / 100)))
    alpha = Image.fromarray((mask * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.8))
    rgba = image.convert("RGB").copy()
    rgba.putalpha(alpha)
    crop = rgba.crop(px)
    return crop, [round(px[0] / w * 100, 3), round(px[1] / h * 100, 3), round(px[2] / w * 100, 3), round(px[3] / h * 100, 3)]


def _pool(a: np.ndarray) -> np.ndarray:
    h, w = a.shape[:2]
    a = np.pad(a, ((0, h % 2), (0, w % 2)) + ((0, 0),) * (a.ndim - 2), mode="edge")
    return (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]) / 4


def _up(a: np.ndarray, shape) -> np.ndarray:
    h, w = shape
    if a.ndim == 2:
        return np.asarray(Image.fromarray(a.astype(np.float32), "F").resize((w, h), Image.BILINEAR))
    return np.dstack([_up(a[..., c], shape) for c in range(a.shape[2])])


def fill(rgb: np.ndarray, hole: np.ndarray, known: np.ndarray | None = None) -> np.ndarray:
    """The hole's pixels filled from their surroundings (push-pull: the known colours are averaged down a pyramid, then
    pulled back up, so a hole takes the smooth colour of what is around it). Known pixels keep their exact colour;
    ``known`` limits what the fill learns from (a pocket in a part is filled from the part, not from the background)."""
    colour = rgb.astype(np.float32)
    weight = (~hole.astype(bool) if known is None else known.astype(bool) & ~hole.astype(bool)).astype(np.float32)
    if weight.all():
        return rgb.copy()
    if not weight.any():
        return np.full_like(rgb, int(colour.mean()))
    levels = [(colour * weight[..., None], weight)]
    while min(levels[-1][1].shape) > 2:
        c, wt = levels[-1]
        wd = _pool(wt)
        cd = _pool(c)
        levels.append((cd, wd))
    c, wt = levels[-1]
    result = c / np.maximum(wt, 1e-6)[..., None]
    for number in range(len(levels) - 2, -1, -1):
        c, wt = levels[number]
        here = c / np.maximum(wt, 1e-6)[..., None]
        trust = (wt if number == 0 else np.clip(wt * 4, 0, 1))[..., None]
        result = trust * here + (1 - trust) * _up(result, wt.shape)
    hole = hole.astype(bool)
    out = rgb.copy()
    out[hole] = np.clip(result[hole], 0, 255).astype(rgb.dtype)
    return out


def _grow(mask: np.ndarray, pixels: int) -> np.ndarray:
    return np.asarray(Image.fromarray((mask * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(2 * pixels + 1))) > 0


SHADE = 0.6       # what a moving part uncovers lies in its shadow: the filled hole is darkened, so it reads as depth (a gap
                  # opening, an empty pocket), not as a pale smear of the neighbours' colours (the ATP demo, 23 November 2026)


def plate(image: Image.Image, masks: list, grow: int = 5, shade: float = SHADE) -> Image.Image:
    """The picture with what lies under ``masks`` filled from around it and shaded (each mask grown by ``grow`` pixels,
    so the part's rim does not stay behind as a ghost)."""
    if not masks:
        return image.convert("RGB")
    hole = np.zeros(masks[0].shape, dtype=bool)
    for m in masks:
        hole |= m.astype(bool)
    if grow:
        hole = _grow(hole, grow)
    filled = fill(np.asarray(image.convert("RGB")), hole).astype(np.float32)
    soft = np.asarray(Image.fromarray((hole * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(grow or 1)),
                      dtype=np.float32)[..., None] / 255.0
    return Image.fromarray(np.clip(filled * (1 - (1 - shade) * soft), 0, 255).astype(np.uint8), "RGB")


def cut_shot(image: Image.Image, parts: list, cutter) -> dict:
    """Every part of one picture. ``parts``: [{id, inside: [[x, y], ...], outside: [[x, y], ...], box: [x0, y0, x1, y1] or
    [], moves: bool, molecule: bool}] in percent; ``outside`` are points on neighbours that touch the part but are not
    it. Each part is cut with and without its box and its outside points, and SAM's most confident mask is kept (a
    molecule never with its box); where two cuts overlap, the pixels go to the smaller part (the more specific cut). Returns {"layers": [{id, image, box, centre, area, score, problems}],
    "plate": image or None}."""
    image = image.convert("RGB")
    cutter.look(image)
    rows, masks = [], []
    for part in parts:
        inside = [list(p) for p in part.get("inside") or []]
        box = list(part.get("box") or []) or None
        row = {"id": part.get("id"), "problems": []}
        rows.append(row)
        if not inside and not box:
            row["problems"] = ["the part was not found in the picture"]
            masks.append(None)
            continue
        if not inside:
            inside = [[(box[0] + box[2]) / 2, (box[1] + box[3]) / 2]]
        outside = [list(p) for p in part.get("outside") or []]
        # SAM is asked a few ways and its most confident mask is kept: other parts' points are never added as "not it"
        # (the ATP demo, 23 November 2026: with them SAM's score fell to 0.09 and the beta took its neighbour), and a
        # molecule (balls and sticks, often in a pocket) is cut without its box, because with the box SAM takes the pocket
        molecule = bool(part.get("molecule"))
        asks = [(outside, None)] + ([] if molecule else [(outside, box)])
        asks += [([], b) for o, b in asks if o]
        raw, score = max((cutter.mask(inside, o, b) for o, b in asks), key=lambda got: got[1])
        row.update(score=round(score, 3), inside=inside, box_pointed=box)
        masks.append(clean(raw, inside, holes=not molecule))
    for i, a in enumerate(masks):                     # an overlap belongs to the smaller cut
        if a is None:
            continue
        for j, b in enumerate(masks):
            if j != i and b is not None and b.sum() < a.sum():
                masks[i] = a = a & ~b
    moving = []
    for i, (part, row, mask) in enumerate(zip(parts, rows, masks)):
        if mask is None:
            continue
        row["area"] = round(float(mask.mean()) * 100, 2)
        box = row.get("box_pointed")
        row["problems"] = check_cut(mask, row.pop("inside"), row.pop("box_pointed"))
        if row["problems"]:
            continue
        held = None                                   # parts drawn inside this one's box: what it holds
        for j, other in enumerate(masks):
            if j != i and other is not None and box and inside_box(box_of(other), box):
                held = other.copy() if held is None else held | other
        if held is not None:                          # grown a little, so the held thing's rim leaves no ghost
            held = _grow(held, 3)
            held = _holes_filled(mask | held) & ~mask
        row["image"], row["box"] = layer(image, mask, inner=held)
        row["centre"] = centre_of(mask)
        if part.get("moves"):
            moving.append(mask if held is None else mask | held)
    rows.sort(key=lambda r: -(r.get("area") or 0))   # the player lays big parts first, what they hold on top
    return {"layers": rows, "plate": plate(image, moving) if moving else None}


def inside_box(inner, outer) -> bool:
    return bool(inner and outer) and inner[0] >= outer[0] - 1 and inner[1] >= outer[1] - 1 \
        and inner[2] <= outer[2] + 1 and inner[3] <= outer[3] + 1


def _holes_filled(mask: np.ndarray) -> np.ndarray:
    try:
        from scipy import ndimage
    except ImportError:
        return mask
    return ndimage.binary_fill_holes(mask)
