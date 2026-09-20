"""H3-001: exhaustive finite-frame 2D layer envelopes, never inferred ink bounds.

CSS individual transforms compose translate -> rotate -> scale, about the center.
The point operation is scale, rotate, translate; inner wrappers apply first.
Reveal clips are conservatively ignored, so this can reject a safe artistic crop
but cannot silently certify an offscreen rectangle because a clip was assumed.
"""
from __future__ import annotations
from dataclasses import asdict
from itertools import combinations
from hashlib import sha256
import math
from .animation_behavior import motion_contract, motion_state
from .qa_common import CompilerQAError, QAFinding, ordered_findings, digest, token
from .artifact_hashing import canonical_json

MAX_FRAMES = 36000
MAX_LAYER_FRAMES = 240000
MAX_PAIR_FRAMES = 2000000
EPSILON_PX = 1e-6


def fail(code: str, message: str):
    raise CompilerQAError(code + ': ' + message)


def finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        fail('LAYOUT_NUMBER_INVALID', name + ' must be finite numeric input')
    return float(value)


def h3_metadata(raw):
    metadata = raw.get('metadata', {}).get('compiler_h3', {})
    if not isinstance(metadata, dict) or set(metadata) - {'layout', 'reduced_motion_variants'}:
        fail('H3_METADATA_UNCONSUMED', 'only layout and reduced_motion_variants are supported')
    return metadata


def layout_policy(raw):
    data = h3_metadata(raw).get('layout', {})
    if not isinstance(data, dict) or set(data) - {'allow_overlap', 'min_text_px', 'min_equation_px'}:
        fail('LAYOUT_POLICY_UNCONSUMED', 'unknown layout policy')
    text = finite(data.get('min_text_px', 12), 'min_text_px')
    math_em = finite(data.get('min_equation_px', 16), 'min_equation_px')
    if not 8 <= text <= 96 or not 8 <= math_em <= 144:
        fail('LAYOUT_READABILITY_POLICY_INVALID', 'unsupported technical pixel floor')
    ids = {e['element_id'] for e in raw['elements']}
    sources = set(raw.get('source_refs', [])) | {v for e in raw['elements'] for v in e.get('source_refs', [])}
    reasons = set(raw.get('reasoning_refs', [])) | {v for e in raw['elements'] for v in e.get('reasoning_refs', [])}
    overlaps = data.get('allow_overlap', [])
    if not isinstance(overlaps, list) or len(overlaps) > 256:
        fail('LAYOUT_OVERLAP_POLICY_INVALID', 'overlap declarations must be a bounded list')
    checked, seen = [], set()
    for row in overlaps:
        if not isinstance(row, dict) or set(row) != {'elements', 'reason', 'source_refs', 'reasoning_refs'}:
            fail('LAYOUT_OVERLAP_POLICY_INVALID', 'each intentional overlap needs a pair and bound justification')
        pair = row['elements']
        if not isinstance(pair, list) or len(pair) != 2 or any(not isinstance(v, str) for v in pair) or len(set(pair)) != 2 or not set(pair) <= ids:
            fail('LAYOUT_OVERLAP_POLICY_INVALID', 'unknown or repeated pair member')
        key = tuple(sorted(pair))
        if key in seen:
            fail('LAYOUT_OVERLAP_POLICY_INVALID', 'duplicate overlap declaration')
        token(row['reason'], 'overlap reason')
        if len(row['reason']) > 2000:
            fail('LAYOUT_OVERLAP_POLICY_INVALID', 'justification exceeds budget')
        for field, allowed in [('source_refs', sources), ('reasoning_refs', reasons)]:
            refs = row[field]
            if not isinstance(refs, list) or not refs or any(not isinstance(v, str) for v in refs) or len(refs) != len(set(refs)) or not set(refs) <= allowed:
                fail('LAYOUT_OVERLAP_PROVENANCE_UNBOUND', field + ' must bind existing provenance')
        seen.add(key)
        checked.append({**row, 'elements': list(key)})
    return {'allow_overlap': sorted(checked, key=lambda r:r['elements']), 'min_text_px':text,
            'min_equation_px': math_em, 'outside_viewport_policy':'reject',
            'intersections':'conservative_full_layer_convex_boxes', 'scope':'technical_not_educational'}


def dimensions(raw, target):
    for key, upper in [('width',8192),('height',8192),('fps',240)]:
        v = getattr(target, key)
        if type(v) is not int or not 1 <= v <= upper:
            fail('LAYOUT_TARGET_INVALID', key + ' outside supported bounds')
    ms = raw.get('duration_ms')
    if type(ms) is not int or ms <= 0:
        fail('LAYOUT_DURATION_INVALID', 'positive integer duration required')
    count = (ms * target.fps + 999) // 1000
    layers = len(raw['elements'])
    if not layers or count > MAX_FRAMES or count * layers > MAX_LAYER_FRAMES or count * layers * (layers-1)//2 > MAX_PAIR_FRAMES:
        fail('LAYOUT_WORK_BUDGET_EXCEEDED', 'no sampled pass substitutes for exhaustive frame coverage')
    return count


def layer_box(element, target):
    box = element.get('normalized_box')
    if not isinstance(box, dict) or set(box) != {'x','y','width','height'}:
        fail('LAYOUT_BINDING_NOT_PROVIDED', 'explicit normalized box required')
    x,y,w,h = (finite(box[k],k) for k in ('x','y','width','height'))
    if min(x,y)<0 or w<=0 or h<=0 or x+w>1+1e-12 or y+h>1+1e-12:
        fail('LAYOUT_BOX_INVALID', 'normalized box is outside the viewport or empty')
    return x*target.width, y*target.height, w*target.width, h*target.height


def transform_point(point, state, width, height):
    x,y = point[0]-width/2, point[1]-height/2
    scale = state.get('scale', 1.)
    x *= scale; y *= scale
    theta = math.radians(state.get('rotate', 0.))
    c,s = math.cos(theta), math.sin(theta)
    return (c*x-s*y+width/2+state.get('translate_x',0.),
            s*x+c*y+height/2+state.get('translate_y',0.))


def frame_layer(element, tracks, frame, target, runtime_targets=None):
    x,y,w,h = layer_box(element, target)
    points = [(0.,0.),(w,0.),(w,h),(0.,h)]
    opacity = 1.
    states = [motion_state(c,frame,target.fps) for c in tracks]
    for state in reversed(states):
        points = [transform_point(p,state,w,h) for p in points]
        opacity *= state.get('opacity',1.)
    if runtime_targets is not None:
        state = runtime_targets.get(element['element_id'], {})
        opacity *= state.get('opacity', 1.)
        if state.get('visible') is False:
            opacity = 0.
    points = [(a+x,b+y) for a,b in points]
    bounds = [min(p[0] for p in points), min(p[1] for p in points),
              max(p[0] for p in points), max(p[1] for p in points)]
    return {'element_id':element['element_id'], 'frame':frame, 'polygon':points,
            'bounds_ltrb':bounds, 'opacity':opacity, 'visible_conservative':opacity>0,
            'source_refs':element.get('source_refs',[]), 'reasoning_refs':element.get('reasoning_refs',[])}


def convex_overlap(a, b):
    """Strict separating-axis overlap. Touching edges have zero occlusion area."""
    for polygon in (a,b):
        for p,q in zip(polygon,polygon[1:]+polygon[:1]):
            nx,ny = -(q[1]-p[1]), q[0]-p[0]
            length = math.hypot(nx,ny)
            if length <= 0:
                fail('LAYOUT_DEGENERATE_POLYGON', 'empty transformed edge')
            nx,ny = nx/length,ny/length
            pa = [x*nx+y*ny for x,y in a]; pb = [x*nx+y*ny for x,y in b]
            if min(max(pa),max(pb))-max(min(pa),min(pb)) <= EPSILON_PX:
                return False
    return True


def iter_frame_layers(raw, target):
    count = dimensions(raw,target)
    indexed = {e['element_id']:[] for e in raw['elements']}
    if len(indexed) != len(raw['elements']):
        fail('LAYOUT_DUPLICATE_ELEMENT', 'element identifiers must be unique')
    for row in raw.get('tracks',[]):
        c = motion_contract(row)
        if c.element_id not in indexed:
            fail('LAYOUT_TRACK_TARGET_MISSING', 'track has no layer')
        indexed[c.element_id].append(c)
    from .frame_runtime_contract import plan_frame_runtime
    from .frame_state_consumer import runtime_at
    plan = plan_frame_runtime(raw, target)
    from .media_presentation import media_presentations, source_video_frame
    media = media_presentations(raw, target, required=False)
    schedules = {r['element_id']:r['presentation'] for r in media['rows'] if r['kind']=='video'} if media else {}
    for frame in range(count):
        targets = runtime_at(plan, frame)['targets'] if plan is not None else {}
        for eid, schedule in schedules.items():
            targets.setdefault(eid, {})
            targets[eid]['visible'] = targets[eid].get('visible', True) and source_video_frame(schedule, frame) is not None
        yield [frame_layer(e,indexed[e['element_id']],frame,target,targets) for e in raw['elements']]


def evaluate_frame_layout(raw, target):
    policy = layout_policy(raw)
    count = dimensions(raw,target)
    allowed = {tuple(r['elements']) for r in policy['allow_overlap']}
    problems, intentional, unions = {}, {}, {}
    stream = sha256(); observed = 0
    def note(code,key,frame):
        item = problems.setdefault((code,key),{'first_frame':frame,'last_frame':frame,'count':0})
        item['last_frame']=frame;item['count']+=1
    for rows in iter_frame_layers(raw,target):
        stream.update(canonical_json(rows));stream.update(b'\n');observed+=1
        for r in rows:
            eid=r['element_id'];box=r['bounds_ltrb']
            if eid not in unions:unions[eid]=list(box)
            else:unions[eid]=[min(unions[eid][0],box[0]),min(unions[eid][1],box[1]),max(unions[eid][2],box[2]),max(unions[eid][3],box[3])]
            if r['visible_conservative'] and (box[0]<-EPSILON_PX or box[1]<-EPSILON_PX or box[2]>target.width+EPSILON_PX or box[3]>target.height+EPSILON_PX):
                note('LAYOUT_OUTSIDE_VIEWPORT',eid,r['frame'])
        for a,b in combinations(rows,2):
            if not a['visible_conservative'] or not b['visible_conservative'] or not convex_overlap(a['polygon'],b['polygon']):continue
            pair=tuple(sorted((a['element_id'],b['element_id'])))
            if pair in allowed:
                row=intentional.setdefault(pair,{'first_frame':a['frame'],'last_frame':a['frame'],'count':0})
                row['last_frame']=a['frame'];row['count']+=1
            else:note('LAYOUT_UNDECLARED_OVERLAP',' / '.join(pair),a['frame'])
    findings = ordered_findings(QAFinding(code,'ERROR',key+' violates layer bounds at '+str(info['count'])+' frames; first='+str(info['first_frame'])+', last='+str(info['last_frame']),'$.layout') for (code,key),info in problems.items())
    return {'schema_version':'bie.frame-layout.v1','scope':'ALL_RENDERED_FRAME_LAYER_BOXES_NOT_INK',
            'scene_identity':digest(raw),'frames_expected':count,'frames_evaluated':observed,
            'frame_rows_sha256':stream.hexdigest(),'layer_bounds':unions,'policy':policy,
            'intentional_overlaps':[{'elements':list(k),**v} for k,v in sorted(intentional.items())],
            'findings':[asdict(f) for f in findings],'passed':not findings and observed==count,
            'paint_verified':False,'continuous_time_verified':False,'accepted':False}
