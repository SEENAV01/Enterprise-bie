"""A cut part that spins, turning for real on screen (Navin, 24 November 2026, on the remade 11.6.3b: "photorealistic hisse
abhi bhi nahi hilte").

A part can face the camera (a wheel seen from the front) or be seen from the side (a dam's turbine runner, the gold
stalk of ATP synthase, a shaft). A wheel that faces us turns in the picture's plane, and the player already rotates it.
A part seen from the side turns about an upright line through it: its blades sweep across from one side to the other
and back around behind. Rotating its picture would make it tumble, and the old fallback (a sheen sliding over it) left
the blades standing still; on the 11.6.3b remake (r2) the turbine's blades did not move by a pixel.

This module looks at the cut part (its pixels, not its words) and, for a part seen from the side, draws the turn as a
strip of frames: each row of the part is a slice of a cylinder, so a pixel at x shows the surface at angle
asin((x - centre) / radius), and turning by phi shows the surface that was at angle - phi. The blades repeat around the
runner, so after one blade's pitch the picture is the same again: the pitch is found in the part itself and the frames
loop over it. The part's outline (its alpha) never changes, so the cut stays exactly where it was in the picture.
"""
from __future__ import annotations

import base64
import io
import math

FRAMES = 16          # frames in one blade pitch; the player loops them
LIMIT = 0.97         # the cylinder is sampled up to this share of its half width (the very rim is all squeeze)
TALL = 0.62          # narrower than this (width / height) is a rod or stalk: seen from the side
WIDE = 1.6           # wider than this is a runner or drum seen from the side, not a wheel facing us
BLEND = 0.35         # share of a pitch over which a blade coming round from behind is blended in
LINED = 0.2          # edges this much in one direction (0: every way, 1: all parallel) are blades seen from the side


def _arrays(image):
    import numpy as np
    from PIL import Image
    if not isinstance(image, Image.Image):
        image = Image.open(image)
    rgba = np.asarray(image.convert("RGBA")).astype(np.float32)
    return rgba, rgba[..., 3] > 128


def lined(rgba, mask) -> float:
    """How much the part's strong edges run one way: about 0.15 for a wheel facing us (spokes and blades every way round),
    0.25 to 0.5 for blades or a helix seen from the side (one slant)."""
    import numpy as np
    gray = rgba[..., :3].mean(axis=2)
    gy, gx = np.gradient(gray)
    inner = mask.copy()
    for _ in range(3):                                   # off the cut's own edge
        inner[1:, :] &= inner[:-1, :].copy()
        inner[:-1, :] &= inner[1:, :].copy()
        inner[:, 1:] &= inner[:, :-1].copy()
        inner[:, :-1] &= inner[:, 1:].copy()
    mag = np.hypot(gx, gy)
    if inner.sum() < 50 or not mag[inner].any():
        return 0.0
    strong = inner & (mag > np.percentile(mag[inner], 70))
    if strong.sum() < 20:
        return 0.0
    angle, weight = 2 * np.arctan2(gy[strong], gx[strong]), mag[strong]
    return float(np.hypot((weight * np.cos(angle)).sum(), (weight * np.sin(angle)).sum()) / weight.sum())


def axis(image) -> str:
    """"facing" (turns in the picture's plane) or "upright" (seen from the side, turns about an up-down line)."""
    import numpy as np
    rgba, mask = _arrays(image)
    if mask.sum() < 50:
        return "facing"
    ys, xs = np.where(mask)
    ratio = (xs.max() - xs.min() + 1) / (ys.max() - ys.min() + 1)
    if ratio < TALL or ratio > WIDE:
        return "upright"
    return "upright" if lined(rgba, mask) >= LINED else "facing"


def _extents(mask):
    import numpy as np
    found = []
    for y in range(mask.shape[0]):
        xs = np.flatnonzero(mask[y])
        if len(xs) >= 4:
            found.append((y, float(xs[0]), float(xs[-1])))
    return found


def _rows(mask):
    """The part as a stack of cylinder slices: (row, centre, radius) for every row it fills. One upright axis for the
    whole part (the middle rows' centre), and each row's radius smoothed over its neighbours, so a ragged cut edge does
    not tear the rows apart as they turn."""
    import numpy as np
    found = _extents(mask)
    if not found:
        return []
    def smooth(values, half):
        padded = np.pad(np.asarray(values, dtype=float), half, mode="edge")
        values = np.array([np.median(padded[i:i + 2 * half + 1]) for i in range(len(values))])
        padded = np.pad(values, half, mode="edge")
        return np.convolve(padded, np.ones(2 * half + 1) / (2 * half + 1), mode="valid")
    # the axis may lean a little (a stalk drawn at a slant), so it follows the rows slowly; the radius follows faster
    centre = smooth([(left + right) / 2 for _, left, right in found], max(3, len(found) // 8))
    radius = smooth([(right - left) / 2 for _, left, right in found], max(2, len(found) // 20))
    return [(y, float(c), float(r), left, right) for (y, left, right), c, r in zip(found, centre, radius)]


def pitch(rgba, mask) -> float:
    """The angle after which the side view repeats (one blade, or one turn of a helix), from the middle rows of the part:
    each row resampled at even angles round the cylinder and correlated with itself shifted."""
    import numpy as np
    rows = [(y, (left + right) / 2, (right - left) / 2) for y, left, right in _extents(mask)]   # each row as it is cut
    if not rows:
        return math.pi / 3
    gray = rgba[..., :3].mean(axis=2)
    n = 128
    thetas = np.linspace(-math.pi / 2 * LIMIT, math.pi / 2 * LIMIT, n)
    step = thetas[1] - thetas[0]
    lags = np.arange(1, round(math.pi / 2.2 / step) + 1)
    middle = rows[len(rows) // 5: len(rows) - len(rows) // 5] or rows
    total = np.zeros(len(lags))
    used = 0
    for y, centre, radius in middle:
        if radius < 6:
            continue
        line = np.interp(centre + radius * np.sin(thetas), np.arange(gray.shape[1]), gray[y])
        line = line - line.mean()
        if float((line * line).sum()) < 1e-3:
            continue
        for i, lag in enumerate(lags):
            a, b = line[:-lag], line[lag:]
            total[i] += float((a * b).sum() / (math.sqrt(float((a * a).sum() * (b * b).sum())) or 1.0))
        used += 1
    if not used:
        return math.pi / 3
    total /= used
    # the first peak after the first dip: a smooth surface is most alike to itself at the smallest shift, so the pitch is
    # where the likeness comes back, not where it is highest
    dip = next((i for i in range(1, len(total) - 1) if total[i] <= total[i - 1] and total[i] <= total[i + 1]), None)
    if dip is None:
        return math.pi / 3
    best = dip + int(np.argmax(total[dip:]))
    return float(lags[best] * step) if total[best] > 0.2 and lags[best] * step >= math.pi / 24 else math.pi / 3


def roll_frames(image, frames: int = FRAMES, period: float | None = None):
    """The part seen from the side, turned through one pitch in ``frames`` steps: a strip of frames side by side (RGBA),
    each with the part's own outline."""
    import numpy as np
    from PIL import Image
    rgba, mask = _arrays(image)
    height, width = mask.shape
    period = period or pitch(rgba, mask)
    strip = np.zeros((height, width * frames, 4), dtype=np.float32)
    columns = np.arange(width, dtype=np.float32)
    rows = _rows(mask)
    low = -math.asin(LIMIT)
    for k in range(frames):
        frame = rgba.copy()
        phi = period * k / frames
        for y, centre, radius, left, right in rows:
            if radius < 2:
                continue
            xs = np.arange(max(0, math.ceil(centre - radius)), min(width - 1, math.floor(centre + radius)) + 1)
            direct = np.arcsin(np.clip((xs - centre) / radius, -LIMIT, LIMIT)) - phi
            # past the left rim the surface comes round from behind: one pitch on, the same blade again; near the rim the
            # two are blended, so a blade that does not repeat exactly shows no seam where it comes round
            other = np.where(direct < low, direct + period * np.ceil((low - direct) / period), direct + period)
            weight = np.clip((direct - low) / (period * BLEND), 0.0, 1.0)
            for c in range(3):
                row = rgba[y, :, c]
                near = np.interp(np.clip(centre + radius * np.sin(direct), left, right), columns, row)
                far = np.interp(np.clip(centre + radius * np.sin(other), left, right), columns, row)
                frame[y, xs, c] = weight * near + (1 - weight) * far
        strip[:, k * width:(k + 1) * width] = frame
    return Image.fromarray(np.clip(strip, 0, 255).astype(np.uint8), "RGBA")


def spin_layer(image, scale: float = 1.0, frames: int = FRAMES) -> dict | None:
    """What the player needs to turn a spinning part seen from the side: {axis, frames (a WEBP strip as a data URI), n,
    pitch (degrees)}; None for a part that faces us (the player turns it in the picture's plane) or when numpy is not on
    this machine (the part then keeps its old way)."""
    try:
        from PIL import Image
        if not isinstance(image, Image.Image):
            image = Image.open(image)
        image = image.convert("RGBA")
        if scale < 1:
            image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))))
        if axis(image) != "upright":
            return None
        rgba, mask = _arrays(image)
        period = pitch(rgba, mask)
        strip = roll_frames(image, frames, period)
    except ImportError:
        return None
    buffer = io.BytesIO()
    strip.save(buffer, "WEBP", quality=85)
    return {"axis": "upright", "n": frames, "pitch": round(math.degrees(period), 1),
            "frames": "data:image/webp;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")}
