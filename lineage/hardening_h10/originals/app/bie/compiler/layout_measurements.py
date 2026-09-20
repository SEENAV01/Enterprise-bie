"""H4-003: exhaustive measured text identity and within-owner collisions.

Rectangles are technical DOM evidence, not glyph-ink segmentation, accessibility
conformance, an authenticated renderer attestation, or educational acceptance.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import asdict
from itertools import combinations

from .content_fit_qa import inspect_content_fit, rect
from .qa_common import CompilerQAError, QAFinding, ordered_findings, digest

MAX_PAIRS = 1_000_000
COLLISION_TOLERANCE_PX = .75
MAP_LIMITS = "Inline geometry only; no basemap. Projected segments are not geodesic paths or distance/area measurements."


def overlap(a: list, b: list) -> bool:
    return min(a[0]+a[2], b[0]+b[2])-max(a[0], b[0]) > COLLISION_TOLERANCE_PX and min(a[1]+a[3], b[1]+b[3])-max(a[1], b[1]) > COLLISION_TOLERANCE_PX


def required_text(element: dict) -> list[str]:
    if element['element_type'] == 'text':
        return [element['props']['text']]
    if element['element_type'] == 'map':
        from .map_geometry import map_geometry
        props = dict(element['props']); props.pop('compiler_layout', None)
        g = map_geometry(props)
        # Projection and coordinates are additionally bound by the governed
        # generator and invariant check. This explicit list checks visible labels.
        return [g.title, *[x['kind'] + ': ' + x['label'] for x in g.layers], g.attribution, MAP_LIMITS]
    return []


def inspect_owner_fit(report: dict, raw: dict, target, manifest_sha256: str) -> dict:
    base = inspect_content_fit(report, raw, target, manifest_sha256)
    findings = [QAFinding(**row) for row in base['findings']]
    by_id = {e['element_id']: e for e in raw['elements']}
    from .frame_runtime_contract import plan_frame_runtime
    from .frame_state_consumer import runtime_at
    runtime_plan = plan_frame_runtime(raw, target)
    runtime_frames = {}
    groups: dict[tuple, dict] = {}
    comparisons = 0
    def note(code, eid, frame, message):
        key = (code, eid)
        group = groups.setdefault(key, {'first_frame':frame, 'frames':set(), 'message':message})
        group['frames'].add(frame)
    for row in report['records']:
        eid, frame = row.get('element_id'), row.get('frame')
        if eid not in by_id or type(frame) is not int: continue
        texts = row.get('rendered_text')
        if not isinstance(texts, list) or len(texts) > 4096 or any(not isinstance(t,str) or len(t) > 100000 for t in texts):
            raise CompilerQAError('OWNER_TEXT_MEASUREMENT_INVALID: bounded rendered_text list required')
        if runtime_plan is not None:
            if frame not in runtime_frames:
                runtime_frames[frame] = runtime_at(runtime_plan, frame)
            values = runtime_frames[frame]
            bound = values['targets'].get(eid, {})
            controlled = bool(bound) or eid == runtime_plan['caption_target_id']
            if controlled and not any(t['element_id'] == eid for t in raw.get('tracks', [])):
                expected_visible = bound.get('visible', True) and bound.get('opacity', 1) != 0
                if row['visible'] != expected_visible:
                    note('LAYOUT_RUNTIME_VISIBILITY_MISMATCH', eid, frame, 'Measured visibility differs from explicit runtime state')
        if not row['visible']: continue
        expected_text = required_text(by_id[eid])
        dynamic_text = False
        if runtime_plan is not None:
            if frame not in runtime_frames:
                runtime_frames[frame] = runtime_at(runtime_plan, frame)
            values = runtime_frames[frame]
            if eid == runtime_plan['caption_target_id']:
                expected_text = [values['caption_text']]; dynamic_text = True
            elif 'text' in values['targets'].get(eid, {}):
                expected_text = [values['targets'][eid]['text']]; dynamic_text = True
        required = Counter(t for t in expected_text if t.strip())
        observed = Counter(t for t in texts if t.strip())
        if dynamic_text and required != observed:
            note('LAYOUT_RUNTIME_CONTENT_MISMATCH', eid, frame, "Painted state/caption does not equal this frame's exact expected text")
        if required - observed:
            note('LAYOUT_VISIBLE_CONTENT_MISSING', eid, frame, 'Required literal content/labels absent from painted DOM')
        boxes = row['text_boxes']; fragments = set()
        for fragment in boxes:
            fid, tid = fragment.get('fragment_id'), fragment.get('text_id')
            if not isinstance(fid, str) or not fid or len(fid) > 512 or not isinstance(tid,str) or not tid or len(tid) > 512:
                raise CompilerQAError('OWNER_TEXT_MEASUREMENT_INVALID: bounded text and fragment identities required')
            if fid in fragments:
                note('LAYOUT_TEXT_FRAGMENT_DUPLICATE', eid, frame, 'Duplicate measured text fragment')
            fragments.add(fid)
        comparisons += len(boxes)*(len(boxes)-1)//2
        if comparisons > MAX_PAIRS:
            raise CompilerQAError('OWNER_COLLISION_BUDGET_EXCEEDED: no sampled pass')
        for a,b in combinations(boxes,2):
            if overlap(a['box'], b['box']):
                # Bidi runs from the same logical Range may touch/overlap while
                # shaping a single line. Distinct logical texts are not exempt.
                if a['text_id'] != b['text_id']:
                    note('LAYOUT_OWNER_TEXT_COLLISION', eid, frame, 'Distinct text nodes overlap inside one owner')
    for (code, eid), group in sorted(groups.items()):
        findings.append(QAFinding(code, 'ERROR', group['message'] + '; element=' + eid + ', first_frame=' + str(group['first_frame']) + ', occurrences=' + str(len(group['frames'])), '$.measurements'))
    final = ordered_findings(findings)
    return {**base, 'schema_version':'bie.owner-fit.v1', 'findings':[asdict(f) for f in final],
            'passed':not any(f.severity == 'ERROR' for f in final), 'pair_comparisons':comparisons,
            'measurement_sha256':digest(report), 'real_remotion_verified':False,
            'release_authorized':False, 'learning_equivalence_verified':False, 'accepted':False}
