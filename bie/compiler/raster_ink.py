"""Frame-complete counterfactual raster diagnostics (COMP H8 / inherited R01).

Every pixel is inspected. An isolated target vs no-target frame identifies its
paint contribution; full vs target-muted identifies surviving contribution.
No OCR, semantic image understanding, WCAG certificate or render authorization.
Policy thresholds are versioned engineering diagnostics, not learning scores.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import math
import os
import stat
import warnings

import numpy as np
from PIL import Image, UnidentifiedImageError

from .qa_common import CompilerQAError, digest


@dataclass(frozen=True)
class RasterPolicy:
    max_pixels: int = 8_294_400
    max_bytes: int = 40_000_000
    max_runs: int = 250_000
    pixel_delta: int = 8
    min_component_pixels: int = 3
    min_visible_strength: float = 0.5
    min_visible_fraction: float = 0.98
    min_component_fraction: float = 0.8

    def __post_init__(self) -> None:
        for name, high in (("max_pixels", 33_177_600), ("max_bytes", 100_000_000),
                           ("max_runs", 1_000_000), ("pixel_delta", 64),
                           ("min_component_pixels", 256)):
            v = getattr(self, name)
            if type(v) is not int or not 1 <= v <= high:
                raise CompilerQAError("RASTER_POLICY_INVALID:" + name)
        for name in ("min_visible_strength", "min_visible_fraction", "min_component_fraction"):
            v = getattr(self, name)
            if type(v) not in (int, float) or not math.isfinite(v) or not 0 < v <= 1:
                raise CompilerQAError("RASTER_POLICY_INVALID:" + name)


def read_png(path: Path | str, *, expected_sha256: str | None = None,
             size: tuple[int, int] | None = None, policy: RasterPolicy | None = None) -> np.ndarray:
    """Read exactly one bounded, opaque sRGB/untagged PNG. No path traversal/symlinks.

    Bytes are opened once with O_NOFOLLOW and hashed before decoding. Non-PNG,
    animated, nonopaque, palette/16-bit or ICC-tagged inputs need normalization by
    a trusted producer; the QA consumer does not silently convert their meaning.
    """
    policy = policy or RasterPolicy()
    p = Path(path).absolute()
    if any(q.is_symlink() for q in (p, *p.parents)):
        raise CompilerQAError("RASTER_SYMLINK_REJECTED")
    try:
        fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise CompilerQAError("RASTER_REGULAR_FILE_REQUIRED")
            if not 0 < st.st_size <= policy.max_bytes:
                raise CompilerQAError("RASTER_BYTE_BUDGET")
            with os.fdopen(fd, 'rb', closefd=False) as f:
                raw = f.read(policy.max_bytes + 1)
            if len(raw) != st.st_size:
                raise CompilerQAError("RASTER_CHANGED_DURING_READ")
        finally:
            os.close(fd)
    except OSError as e:
        raise CompilerQAError("RASTER_FILE_UNAVAILABLE") from e
    if expected_sha256 is not None and (not isinstance(expected_sha256, str) or sha256(raw).hexdigest() != expected_sha256):
        raise CompilerQAError("RASTER_HASH_MISMATCH")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as im:
                if im.format != 'PNG' or im.mode not in {'RGB', 'RGBA'} or getattr(im, 'n_frames', 1) != 1:
                    raise CompilerQAError("RASTER_STATIC_RGB_PNG_REQUIRED")
                w, h = im.size
                if w * h > policy.max_pixels:
                    raise CompilerQAError("RASTER_PIXEL_BUDGET")
                if size is not None and im.size != size:
                    raise CompilerQAError("RASTER_SIZE_MISMATCH")
                if im.info.get('icc_profile') is not None or ('gamma' in im.info and abs(im.info['gamma'] - 0.45455) > 1e-4):
                    raise CompilerQAError("RASTER_COLOR_PROFILE_UNRESOLVED")
                im.verify()
            with Image.open(BytesIO(raw)) as im:
                im.load()
                arr = np.asarray(im, dtype=np.uint8).copy()
            if arr.shape[2] == 4:
                if not np.all(arr[:, :, 3] == 255):
                    raise CompilerQAError("RASTER_OPAQUE_COMPOSITE_REQUIRED")
                arr = arr[:, :, :3].copy()
            return arr
    except CompilerQAError:
        raise
    except (OSError, ValueError, SyntaxError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as e:
        raise CompilerQAError("RASTER_DECODE_FAILED") from e


def _rgb(a: np.ndarray, policy: RasterPolicy) -> np.ndarray:
    if not isinstance(a, np.ndarray) or a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] != 3 or not a.shape[0] or not a.shape[1]:
        raise CompilerQAError("RASTER_RGB_ARRAY_REQUIRED")
    if a.shape[0] * a.shape[1] > policy.max_pixels:
        raise CompilerQAError("RASTER_PIXEL_BUDGET")
    return a


def difference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.max(np.abs(a.astype(np.int16) - b.astype(np.int16)), axis=2)


def connected_ink(mask: np.ndarray, visible: np.ndarray | None = None, *, max_runs: int = 250_000) -> list[dict]:
    """Deterministic 8-connected run-length union; no discarded small components."""
    if not isinstance(mask, np.ndarray) or mask.ndim != 2 or mask.dtype != np.bool_:
        raise CompilerQAError("RASTER_MASK_REQUIRED")
    if visible is None:
        visible = mask
    if not isinstance(visible, np.ndarray) or visible.shape != mask.shape or visible.dtype != np.bool_ or type(max_runs) is not int or max_runs < 1:
        raise CompilerQAError("RASTER_MASK_MISMATCH")
    parents: list[int] = []
    rows: list[tuple[int, int, int, int]] = []
    previous: list[tuple[int, int, int]] = []

    def root(k: int) -> int:
        while parents[k] != k:
            parents[k] = parents[parents[k]]
            k = parents[k]
        return k

    for y in range(mask.shape[0]):
        changes = np.flatnonzero(np.diff(np.pad(mask[y].astype(np.int8), (1, 1))))
        current: list[tuple[int, int, int]] = []
        j = 0
        for left, stop in zip(changes[::2], changes[1::2]):
            x0, x1 = int(left), int(stop)  # half-open
            k = len(parents)
            if k >= max_runs:
                raise CompilerQAError("RASTER_COMPONENT_WORK_BUDGET")
            parents.append(k)
            rows.append((y, x0, x1, int(visible[y, x0:x1].sum())))
            while j < len(previous) and previous[j][1] < x0:
                j += 1
            t = j
            while t < len(previous) and previous[t][0] <= x1:
                a, b = root(k), root(previous[t][2])
                if a != b:
                    parents[max(a, b)] = min(a, b)
                t += 1
            current.append((x0, x1, k))
        previous = current
    stats: dict[int, list[int]] = {}
    for k, (y, x0, x1, seen) in enumerate(rows):
        key = root(k)
        if key not in stats:
            stats[key] = [x0, y, x1, y + 1, x1 - x0, seen]
        else:
            s = stats[key]
            s[:] = [min(s[0], x0), min(s[1], y), max(s[2], x1), max(s[3], y + 1), s[4] + x1 - x0, s[5] + seen]
    return [{'box': [s[0], s[1], s[2] - s[0], s[3] - s[1]], 'pixels': s[4],
             'visible_pixels': s[5], 'visible_fraction': s[5] / s[4]}
            for _, s in sorted(stats.items())]


def counterfactual_ink(full: np.ndarray, background: np.ndarray, isolated: np.ndarray,
                       muted: np.ndarray, *, target_id: str, originally_visible: bool = True, require_nonempty: bool = True,
                       policy: RasterPolicy | None = None) -> tuple[dict, np.ndarray]:
    policy = policy or RasterPolicy()
    if not isinstance(target_id, str) or not target_id or type(originally_visible) is not bool or type(require_nonempty) is not bool:
        raise CompilerQAError("RASTER_TARGET_INVALID")
    arrays = [_rgb(a, policy) for a in (full, background, isolated, muted)]
    if len({a.shape for a in arrays}) != 1:
        raise CompilerQAError("RASTER_SIZE_MISMATCH")
    expected_strength = difference(isolated, background)
    actual_strength = difference(full, muted)
    expected = expected_strength >= policy.pixel_delta
    visible = expected & (actual_strength >= np.maximum(policy.pixel_delta, expected_strength * policy.min_visible_strength))
    components = connected_ink(expected, visible, max_runs=policy.max_runs)
    total = int(expected.sum())
    retained = int(visible.sum())
    findings: list[dict] = []
    if require_nonempty and not total:
        findings.append({'code': 'RASTER_NO_DISTINGUISHABLE_INK', 'target_id': target_id})
    if not originally_visible and total:
        findings.append({'code': 'RASTER_HIDDEN_TARGET_PAINTS', 'target_id': target_id})
    if total and retained / total < policy.min_visible_fraction:
        findings.append({'code': 'RASTER_PARTIALLY_OCCLUDED', 'target_id': target_id, 'visible_fraction': retained / total})
    for i, c in enumerate(components):
        if c['pixels'] >= policy.min_component_pixels and c['visible_fraction'] < policy.min_component_fraction:
            findings.append({'code': 'RASTER_INK_COMPONENT_LOST', 'target_id': target_id, 'component': i, 'box': c['box']})
    # The real image may contain paint this target occludes. Never call full-muted
    # pixels outside the isolated mask "target ink": their ownership is ambiguous.
    report = {'schema_version': 'bie.counterfactual-ink.v1', 'target_id': target_id,
              'passed': not findings, 'findings': findings, 'require_nonempty': require_nonempty, 'expected_pixels': total,
              'visible_pixels': retained, 'visible_fraction': retained / total if total else None,
              'components': components, 'pixel_count_inspected': full.shape[0] * full.shape[1],
              'mask_sha256': sha256(np.packbits(expected).tobytes()).hexdigest(),
              'policy': asdict(policy), 'policy_sha256': digest(asdict(policy)),
              'scope': 'PIXEL_CONTRIBUTION_NOT_SEMANTIC_IMAGE_UNDERSTANDING', 'accepted': False}
    return report, expected
