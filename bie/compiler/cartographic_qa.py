"""H8 projected-feature raster resolution checks for existing inline maps.

No basemap invention, geographic truth assertion, universal readability score,
color-only identification, OCR, or automatic removal of coincident features.
Thresholds are explicit engineering floors in final output pixels.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
import numpy as np
from .qa_common import CompilerQAError, digest


@dataclass(frozen=True)
class CartographicPolicy:
    min_point_diameter_px: int = 3
    min_route_span_px: int = 4
    min_polygon_span_px: int = 3
    min_feature_pixels: int = 3
    point_separation_px: int = 2
    max_route_overlap: float = 0.8

    def __post_init__(self):
        for name in ('min_point_diameter_px', 'min_route_span_px', 'min_polygon_span_px', 'min_feature_pixels', 'point_separation_px'):
            v = getattr(self, name)
            if type(v) is not int or not 1 <= v <= 64:
                raise CompilerQAError('CARTOGRAPHIC_POLICY_INVALID:' + name)
        if type(self.max_route_overlap) not in (float, int) or not math.isfinite(self.max_route_overlap) or not 0 < self.max_route_overlap <= 1:
            raise CompilerQAError('CARTOGRAPHIC_POLICY_INVALID:max_route_overlap')


def _near(a: np.ndarray, b: np.ndarray, radius: int) -> bool:
    h, w = a.shape
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            y0, y1 = max(0, dy), min(h, h + dy)
            x0, x1 = max(0, dx), min(w, w + dx)
            if y1 > y0 and x1 > x0 and np.any(a[y0:y1, x0:x1] & b[y0-dy:y1-dy, x0-dx:x1-dx]):
                return True
    return False


def inspect_cartographic_masks(features: list[dict], masks: dict[str, np.ndarray], *,
                                policy: CartographicPolicy | None = None) -> dict:
    policy = policy or CartographicPolicy()
    if not isinstance(masks, dict):
        raise CompilerQAError('CARTOGRAPHIC_MASK_COVERAGE')
    if not isinstance(features, list) or len(features) > 128:
        raise CompilerQAError('CARTOGRAPHIC_FEATURE_BUDGET')
    ids: set[str] = set()
    shape = None
    findings, rows = [], []
    for f in features:
        if not isinstance(f, dict) or set(f) != {'target_id', 'element_id', 'layer_id', 'kind', 'source_ref', 'visible'}:
            raise CompilerQAError('CARTOGRAPHIC_FEATURE_IDENTITY')
        tid = f['target_id']
        if not isinstance(tid, str) or tid in ids or f['kind'] not in {'route', 'point', 'polygon'} or type(f['visible']) is not bool:
            raise CompilerQAError('CARTOGRAPHIC_FEATURE_IDENTITY')
        if any(not isinstance(f[k], str) or not f[k] for k in ('element_id', 'layer_id')):
            raise CompilerQAError('CARTOGRAPHIC_FEATURE_IDENTITY')
        if f['source_ref'] is not None and not isinstance(f['source_ref'], str):
            raise CompilerQAError('CARTOGRAPHIC_SOURCE_INVALID')
        ids.add(tid)
        a = masks.get(tid)
        if not isinstance(a, np.ndarray) or a.dtype != np.bool_ or a.ndim != 2 or not a.size or a.size > 8_294_400:
            raise CompilerQAError('CARTOGRAPHIC_MASK_INVALID')
        if shape is None:
            shape = a.shape
        if shape != a.shape:
            raise CompilerQAError('CARTOGRAPHIC_MASK_MISMATCH')
        y, x = np.nonzero(a)
        width = int(x.max() - x.min() + 1) if len(x) else 0
        height = int(y.max() - y.min() + 1) if len(y) else 0
        count = int(a.sum())
        rows.append({**f, 'pixels': count, 'width_px': width, 'height_px': height})
        if not f['visible']:
            continue
        code = None
        if count < policy.min_feature_pixels:
            code = 'MAP_FEATURE_NO_RESOLVED_INK'
        elif f['kind'] == 'point' and min(width, height) < policy.min_point_diameter_px:
            code = 'MAP_POINT_BELOW_PIXEL_FLOOR'
        elif f['kind'] == 'route' and max(width, height) < policy.min_route_span_px:
            code = 'MAP_ROUTE_COLLAPSED'
        elif f['kind'] == 'polygon' and min(width, height) < policy.min_polygon_span_px:
            code = 'MAP_POLYGON_COLLAPSED'
        if code:
            findings.append({'code': code, 'target_id': tid, 'element_id': f['element_id'], 'layer_id': f['layer_id']})
    if set(masks) != ids:
        raise CompilerQAError('CARTOGRAPHIC_MASK_COVERAGE')
    for i, a in enumerate(features):
        for b in features[i+1:]:
            if a['element_id'] != b['element_id'] or not a['visible'] or not b['visible']:
                continue
            ma, mb = masks[a['target_id']], masks[b['target_id']]
            if not ma.any() or not mb.any():
                continue
            code = None
            if a['kind'] == b['kind'] == 'point' and _near(ma, mb, policy.point_separation_px):
                code = 'MAP_POINTS_VISUALLY_UNRESOLVED'
            if a['kind'] == b['kind'] == 'route':
                overlap = int((ma & mb).sum()) / min(int(ma.sum()), int(mb.sum()))
                if overlap >= policy.max_route_overlap:
                    code = 'MAP_ROUTES_VISUALLY_AMBIGUOUS'
            if code:
                findings.append({'code': code, 'element_id': a['element_id'], 'targets': [a['target_id'], b['target_id']]})
    return {'schema_version': 'bie.cartographic-raster.v1', 'passed': not findings,
            'findings': findings, 'features': rows, 'policy': asdict(policy),
            'policy_sha256': digest(asdict(policy)), 'accepted': False,
            'scope': 'PROJECTED_FEATURE_PIXEL_RESOLUTION_NOT_MAP_TRUTH_OR_TEACHING_EQUIVALENCE'}
