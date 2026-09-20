"""Source-bound all-frame raster capture consumer shared by diagnostic/real producers.

A returned JSON report is never a production authorization witness. The actual
render path must create its existing in-process witness after this check passes.
"""
from __future__ import annotations
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import math
import numpy as np
from .qa_common import CompilerQAError, digest
from .raster_ink import RasterPolicy, read_png, counterfactual_ink
from .cartographic_qa import CartographicPolicy, inspect_cartographic_masks

REAL_SCOPE = 'REAL_REMOTION_COUNTERFACTUAL_PIXELS'
DIAGNOSTIC_SCOPE = 'REAL_CHROMIUM_PIXELS_EXPLICIT_REACT_REMOTION_DOUBLES'
MAX_CAPTURE_PIXELS = 4_000_000_000


def build_raster_targets(raw: dict) -> list[dict]:
    from .map_geometry import map_geometry
    if not isinstance(raw, dict) or not isinstance(raw.get('elements'), list) or not raw['elements']:
        raise CompilerQAError('RASTER_SCENE_INVALID')
    targets, ids = [], set()
    for i, e in enumerate(raw['elements']):
        eid = e.get('element_id')
        if not isinstance(eid, str) or not eid or eid in ids:
            raise CompilerQAError('RASTER_ELEMENT_IDENTITY')
        ids.add(eid)
        targets.append({'target_id': f'owner:{i}', 'element_id': eid, 'layer_id': None,
                        'kind': 'owner', 'source_refs': list(e.get('source_refs', [])), 'source_ref': None})
        if e['element_type'] == 'map':
            props = dict(e['props']); props.pop('compiler_layout', None)
            geometry = map_geometry(props)
            for j, layer in enumerate(geometry.layers):
                targets.append({'target_id': f'map:{i}:{j}', 'element_id': eid, 'layer_id': layer['layer_id'],
                                'kind': layer['kind'], 'source_refs': list(e.get('source_refs', [])), 'source_ref': layer['source_ref']})
    if len(targets) > 128:
        raise CompilerQAError('RASTER_TARGET_BUDGET')
    return targets


def capture_budget(width: int, height: int, frames: int, target_count: int) -> int:
    if any(type(v) is not int or v < 1 for v in (width, height, frames, target_count)) or frames > 2400 or target_count > 128:
        raise CompilerQAError('RASTER_CAPTURE_DIMENSIONS')
    if width * height > RasterPolicy().max_pixels:
        raise CompilerQAError('RASTER_PIXEL_BUDGET')
    n = width * height * frames * (2 + 3 * target_count)
    if n > MAX_CAPTURE_PIXELS:
        raise CompilerQAError('RASTER_CAPTURE_WORK_BUDGET_NO_SAMPLED_PASS')
    return n


def frame_file(frame: int, kind: str, index: int | None = None) -> str:
    if kind not in {'full', 'repeat', 'baseline', 'isolated', 'muted'}:
        raise CompilerQAError('RASTER_MODE_INVALID')
    if type(frame) is not int or frame < 0:
        raise CompilerQAError('RASTER_FRAME_INVALID')
    if kind in {'baseline', 'isolated', 'muted'}:
        if type(index) is not int or index < 0:
            raise CompilerQAError('RASTER_TARGET_INDEX')
        return f'frame-{frame:06d}-target-{index:03d}-{kind}.png'
    return f'frame-{frame:06d}-{kind}.png'


def required_paint(raw: dict, target, frame: int) -> dict[str, bool]:
    """Source-driven empty-caption/hidden-state/fully clipped-frame exemptions.

    Fractions below the explicit pixel delta are examined but need not have a
    distinguishable pixel. This does not allow a visible source state to vanish.
    """
    from .frame_runtime_contract import plan_frame_runtime
    from .frame_state_consumer import runtime_at
    from .animation_behavior import motion_contract, motion_state
    plan = plan_frame_runtime(raw, target)
    values = runtime_at(plan, frame) if plan is not None else None
    requirements = {}
    for e in raw['elements']:
        eid = e['element_id']; needed = True; alpha = 1.0
        if e['element_type'] == 'text':
            text = e['props'].get('text', '')
            if values is not None:
                if eid == plan['caption_target_id']: text = values['caption_text']
                else: text = values['targets'].get(eid, {}).get('text', text)
            needed = bool(text.strip())
        if values is not None:
            bound = values['targets'].get(eid, {})
            needed = needed and bound.get('visible', True)
            alpha *= bound.get('opacity', 1)
        for t in raw.get('tracks', []):
            if t['element_id'] != eid: continue
            state = motion_state(motion_contract(t), frame, target.fps)
            alpha *= state.get('opacity', 1)
            v = state.get('inset_percent', [0,0,0,0])
            if v[0]+v[2] >= 100 or v[1]+v[3] >= 100: needed = False
        requirements[eid] = bool(needed and alpha >= RasterPolicy().pixel_delta / 255)
    return requirements


def inspect_counterfactual_capture(root: Path | str, capture: dict, raw: dict, target, manifest_sha256: str, *,
                                    expected_scope: str, policy: RasterPolicy | None = None,
                                    cartographic_policy: CartographicPolicy | None = None) -> dict:
    policy = policy or RasterPolicy(); cartographic_policy = cartographic_policy or CartographicPolicy()
    if expected_scope not in {REAL_SCOPE, DIAGNOSTIC_SCOPE}:
        raise CompilerQAError('RASTER_SCOPE_INVALID')
    targets = build_raster_targets(raw)
    n = (raw['duration_ms'] * target.fps + 999) // 1000
    work = capture_budget(target.width, target.height, n, len(targets))
    required = {'schema_version', 'scope', 'scene_sha256', 'manifest_sha256', 'width', 'height', 'fps', 'frame_count', 'targets', 'frames', 'browser_errors'}
    if not isinstance(capture, dict) or set(capture) != required:
        raise CompilerQAError('RASTER_CAPTURE_FIELDS')
    if capture['schema_version'] != 'bie.counterfactual-capture.v1' or capture['scope'] != expected_scope:
        raise CompilerQAError('RASTER_SCOPE_MISMATCH')
    if capture['scene_sha256'] != digest(raw) or capture['manifest_sha256'] != manifest_sha256 or capture['targets'] != targets:
        raise CompilerQAError('RASTER_SOURCE_IDENTITY')
    if any(type(capture[k]) is not int for k in ('width','height','fps','frame_count')) or (capture['width'],capture['height'],capture['fps'],capture['frame_count']) != (target.width,target.height,target.fps,n):
        raise CompilerQAError('RASTER_TARGET_DIMENSIONS')
    if capture['browser_errors'] != []:
        raise CompilerQAError('RASTER_BROWSER_ERRORS')
    rows = capture['frames']
    if not isinstance(rows, list) or len(rows) != n:
        raise CompilerQAError('RASTER_FRAME_COVERAGE')
    root = Path(root).absolute()
    if root.is_symlink() or any(p.is_symlink() for p in root.parents):
        raise CompilerQAError('RASTER_SYMLINK_REJECTED')
    filenames: set[str] = set()
    images: list[dict] = []
    findings, reports = [], []
    for f, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {'frame', 'full', 'repeat', 'inventory', 'targets'} or type(row['frame']) is not int or row['frame'] != f:
            raise CompilerQAError('RASTER_FRAME_IDENTITY')
        inventory = row['inventory']
        if not isinstance(inventory, list) or len(inventory) != len(targets):
            raise CompilerQAError('RASTER_INVENTORY_COVERAGE')
        for spec, inv in zip(targets, inventory):
            if not isinstance(inv, dict) or set(inv) != {'target_id','visible','unresolved_effect','box'} or inv['target_id'] != spec['target_id']:
                raise CompilerQAError('RASTER_INVENTORY_IDENTITY')
            if type(inv['visible']) is not bool or type(inv['unresolved_effect']) is not bool or not isinstance(inv['box'],list) or len(inv['box'])!=4 or any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>1e7 for x in inv['box']):
                raise CompilerQAError('RASTER_INVENTORY_INVALID')
            if inv['box'][2] < 0 or inv['box'][3] < 0:
                raise CompilerQAError('RASTER_INVENTORY_INVALID')
            if inv['unresolved_effect']:
                findings.append({'code':'RASTER_EFFECT_ATTRIBUTION_UNVERIFIED','frame':f,'target_id':spec['target_id']})
        def image(rec, kind, index=None):
            expected = frame_file(f, kind, index)
            if not isinstance(rec,dict) or set(rec) != {'file','sha256'} or rec['file'] != expected or expected in filenames:
                raise CompilerQAError('RASTER_IMAGE_IDENTITY')
            filenames.add(expected)
            a = read_png(root/expected, expected_sha256=rec['sha256'], size=(target.width,target.height),policy=policy)
            images.append({'file':expected,'sha256':rec['sha256']})
            return a
        full, repeat = image(row['full'],'full'), image(row['repeat'],'repeat')
        if not np.array_equal(full, repeat):
            raise CompilerQAError('RASTER_COUNTERFACTUAL_DID_NOT_RESTORE')
        target_rows = row['targets']
        if not isinstance(target_rows,list) or len(target_rows) != len(targets):
            raise CompilerQAError('RASTER_TARGET_COVERAGE')
        per_frame, masks, features = [], {}, []
        required = required_paint(raw, target, f)
        for i, (spec, inv, entry) in enumerate(zip(targets, inventory, target_rows)):
            if not isinstance(entry,dict) or set(entry) != {'target_id','baseline','isolated','muted'} or entry['target_id'] != spec['target_id']:
                raise CompilerQAError('RASTER_TARGET_IDENTITY')
            base, alone, absent = (image(entry[k],k,i) for k in ('baseline','isolated','muted'))
            result, mask = counterfactual_ink(full,base,alone,absent,target_id=spec['target_id'],originally_visible=inv['visible'],require_nonempty=required[spec['element_id']],policy=policy)
            per_frame.append(result)
            findings.extend({**x,'frame':f,'element_id':spec['element_id']} for x in result['findings'])
            if spec['layer_id'] is not None:
                features.append({k:spec[k] for k in ('target_id','element_id','layer_id','kind','source_ref')} | {'visible': required[spec['element_id']]})
                masks[spec['target_id']] = mask
        cart = inspect_cartographic_masks(features,masks,policy=cartographic_policy)
        findings.extend({**x,'frame':f} for x in cart['findings'])
        reports.append({'frame':f,'targets':per_frame,'cartographic':cart})
    return {'schema_version':'bie.counterfactual-analysis.v1','passed':not findings,'findings':findings,
            'frames':reports,'frame_count':n,'target_frame_records':n*len(targets),
            'capture_pixel_budget':work,'image_count':len(images),'images_sha256':digest(images),
            'capture_sha256':digest(capture),'source_manifest_sha256':manifest_sha256,
            'scene_sha256':digest(raw),'scope':expected_scope,'accepted':False,
            'release_authorized':False,'limits':'Complete pixel-contribution diagnostics for captured targets. Not arbitrary image meaning, human readability or educational equivalence.'}
