"""H6-001: bounded, source-bound frame runtime contracts.

State changes are declarative assignments, not executable handlers. Frame intervals
are half-open and quantized using ceiling at both boundaries (never early).
A plan is technical source evidence, never speech/content/rights acceptance.
"""
from __future__ import annotations
from copy import deepcopy
import math
import re
from .qa_common import CompilerQAError, digest

SCHEMA = 'bie.comp-frame-runtime.v1'
MAX_EVENTS = 1024
MAX_STATES = 128
MAX_CUES = 256
MAX_TEXT = 20000
_ID = re.compile(r'[A-Za-z][A-Za-z0-9_.:-]{0,127}\Z')
_SHA = re.compile(r'[0-9a-f]{64}\Z')


def fail(code, message):
    raise CompilerQAError(code + ': ' + message)


def fields(value, allowed, required, label):
    if not isinstance(value, dict) or set(value) - set(allowed) or not set(required) <= set(value):
        fail('FRAME_RUNTIME_FIELDS', label + ' has missing, unknown or non-object fields')
    return value


def ident(value, label):
    if not isinstance(value, str) or not _ID.fullmatch(value) or any(
        x in {'__proto__', 'constructor', 'prototype'} for x in re.split(r'[.:]', value)
    ):
        fail('FRAME_RUNTIME_ID', label + ' must be a bounded safe identifier')
    return value


def integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        fail('FRAME_RUNTIME_INTEGER', label + ' out of range')
    return value


def number(value, low, high, label):
    if type(value) not in (int, float) or not low <= value <= high or not math.isfinite(value):
        fail('FRAME_RUNTIME_NUMBER', label + ' must be finite and in range')
    return value


def text(value, label, *, blank=False):
    if not isinstance(value, str) or len(value) > MAX_TEXT or (not blank and not value.strip()):
        fail('FRAME_RUNTIME_TEXT', label + ' must be bounded text')
    if any(ord(x) < 32 and x not in '\n\r\t' for x in value) or any(0xD800 <= ord(x) <= 0xDFFF for x in value):
        fail('FRAME_RUNTIME_TEXT', label + ' contains unsupported control/surrogate characters')
    return value


def refs(value, owner, label):
    for key in ('source_refs', 'reasoning_refs'):
        r = value.get(key)
        if (not isinstance(r, list) or not r or any(not isinstance(v, str) for v in r)
                or len(r) != len(set(r)) or not set(r) <= set(owner.get(key, []))):
            fail('FRAME_RUNTIME_PROVENANCE', label + ': ' + key + ' is not bound to source')


def frame_at(ms, fps):
    return (ms * fps + 999) // 1000


def scalar(value):
    if isinstance(value, str):
        return text(value, 'state value')
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        return number(value, -1e12, 1e12, 'state value')
    fail('FRAME_RUNTIME_VALUE', 'only literal text, booleans and bounded numbers are supported')


def transformed(value, prop, transform):
    if transform not in {'identity', 'clamp01'} or (transform == 'clamp01' and prop != 'opacity'):
        fail('FRAME_RUNTIME_TRANSFORM', 'no implicit coercion or executable transformations')
    if prop == 'text':
        return text(value, 'bound text')
    if prop == 'visible':
        if type(value) is not bool:
            fail('FRAME_RUNTIME_TYPE', 'visible requires a JSON boolean')
        return value
    if prop == 'opacity':
        number(value, -1e12, 1e12, 'opacity')
        if transform == 'clamp01':
            return max(0, min(1, value))
        return number(value, 0, 1, 'opacity')
    fail('FRAME_RUNTIME_PROPERTY', 'supported state properties are text, visible and opacity')


def _items(value, maximum, label):
    if not isinstance(value, list) or len(value) > maximum or not all(isinstance(v, dict) for v in value):
        fail('FRAME_RUNTIME_BUDGET', label + ' must be a bounded list of objects')
    return value


def plan_frame_runtime(raw, target):
    """Return None for legacy inputs; never implicitly consume an old contract."""
    # The optional self-fingerprint is derived, not a second source of identity.
    raw = {k: v for k, v in raw.items() if k != 'fingerprint'}
    cfg = raw.get('metadata', {}).get('compiler_h6')
    if cfg is None:
        return None
    fields(cfg, {'schema_version', 'initial_state', 'state_lineage', 'narration_revision',
                 'narration_texts', 'audio_assets', 'audio_segments', 'caption_target_id'}, {'schema_version'}, 'compiler_h6')
    if cfg['schema_version'] != SCHEMA:
        fail('FRAME_RUNTIME_VERSION', 'unsupported version')
    fps = integer(target.fps, 1, 240, 'fps')
    duration_ms = integer(raw['duration_ms'], 1, 24 * 3600 * 1000, 'duration')
    frames = frame_at(duration_ms, fps)
    elems = {e['element_id']: e for e in raw['elements']}
    states = deepcopy(cfg.get('initial_state', {}))
    lineage = cfg.get('state_lineage', {})
    if not isinstance(states, dict) or len(states) > MAX_STATES or not isinstance(lineage, dict) or set(states) != set(lineage):
        fail('FRAME_RUNTIME_STATES', 'every state requires exactly one lineage record')
    declared = raw.get('metadata', {}).get('state_paths', [])
    if not isinstance(declared, list) or len(set(declared)) != len(declared) or set(declared) != set(states):
        fail('FRAME_RUNTIME_STATE_COVERAGE', 'declared state paths and initial values must match exactly')
    for key, value in states.items():
        ident(key, 'state path'); scalar(value)
        fields(lineage[key], {'source_refs', 'reasoning_refs'}, {'source_refs', 'reasoning_refs'}, 'state lineage')
        refs(lineage[key], raw, 'state ' + key)

    bindings, seen_ids, targets = [], set(), set()
    for b in _items(raw.get('state_bindings', []), MAX_STATES * 3, 'state bindings'):
        fields(b, {'binding_id', 'state_path', 'target_id', 'property_name', 'transform', 'default_value', 'read_only'},
               {'binding_id', 'state_path', 'target_id', 'property_name'}, 'state binding')
        bid = ident(b['binding_id'], 'binding id'); path = ident(b['state_path'], 'state path'); eid = ident(b['target_id'], 'target id')
        if bid in seen_ids or (eid, b['property_name']) in targets:
            fail('FRAME_RUNTIME_BINDING_CONFLICT', 'duplicate identity/property writer')
        seen_ids.add(bid); targets.add((eid, b['property_name']))
        if path not in states or eid not in elems:
            fail('FRAME_RUNTIME_BINDING_TARGET', 'unknown state or element')
        if type(b.get('read_only', True)) is not bool or b.get('read_only', True) is not True:
            fail('FRAME_RUNTIME_INTERACTIVE_WRITE_UNSUPPORTED', 'offline frame bindings must be read-only')
        prop = b['property_name']; transform = b.get('transform', 'identity')
        value = transformed(states[path], prop, transform)
        if 'default_value' in b and (type(b['default_value']) is not type(states[path]) or b['default_value'] != states[path]):
            fail('FRAME_RUNTIME_DEFAULT_MISMATCH', 'default may not override the declared initial state')
        if prop == 'text' and (elems[eid]['element_type'] != 'text' or value != elems[eid]['props'].get('text')):
            fail('FRAME_RUNTIME_TEXT_INITIAL_MISMATCH', 'initial bound text must match the existing text element')
        if prop in {'opacity', 'visible'} and any(t['element_id'] == eid for t in raw.get('tracks', [])):
            fail('FRAME_RUNTIME_PROPERTY_CONFLICT', 'state visibility/opacity plus animation is not silently composed')
        bindings.append({'binding_id': bid, 'state_path': path, 'target_id': eid, 'property_name': prop,
                         'transform': transform, 'source_refs': list(elems[eid]['source_refs']),
                         'reasoning_refs': list(elems[eid]['reasoning_refs'])})
    if {b['state_path'] for b in bindings} != set(states):
        fail('FRAME_RUNTIME_UNUSED_STATE', 'all declared state paths need a visible consumer')

    events, ids, writes = [], set(), set()
    for e in _items(raw.get('events', []), MAX_EVENTS, 'events'):
        fields(e, {'event_id', 'at_ms', 'event_type', 'target_ids', 'payload'},
               {'event_id', 'at_ms', 'event_type', 'target_ids', 'payload'}, 'event')
        eid = ident(e['event_id'], 'event id')
        if eid in ids:
            fail('FRAME_RUNTIME_EVENT_DUPLICATE', eid)
        ids.add(eid)
        if e['event_type'] != 'state.set':
            fail('FRAME_RUNTIME_EVENT_UNSUPPORTED', 'only pure state.set events are supported')
        p = fields(e['payload'], {'state_path', 'value', 'source_refs', 'reasoning_refs'},
                   {'state_path', 'value', 'source_refs', 'reasoning_refs'}, 'event payload')
        path = ident(p['state_path'], 'event state path')
        if path not in states:
            fail('FRAME_RUNTIME_EVENT_STATE', 'unknown state path')
        value = scalar(p['value'])
        if type(value) is not type(states[path]) and not (type(value) in (int, float) and type(states[path]) in (int, float)):
            fail('FRAME_RUNTIME_TYPE', 'events cannot change the declared state type')
        refs(p, raw, eid)
        bs = [b for b in bindings if b['state_path'] == path]
        expected = sorted({b['target_id'] for b in bs})
        if not isinstance(e['target_ids'], list) or sorted(e['target_ids']) != expected:
            fail('FRAME_RUNTIME_EVENT_TARGETS', 'event targets must exactly cover consumers of the changed state')
        for b in bs:
            transformed(value, b['property_name'], b['transform'])
        ms = integer(e['at_ms'], 0, duration_ms - 1, 'event at_ms'); f = frame_at(ms, fps)
        if f >= frames:
            fail('FRAME_RUNTIME_EVENT_UNSAMPLED', 'event has no rendered frame')
        if (f, path) in writes:
            fail('FRAME_RUNTIME_EVENT_COLLISION', 'two writes to one state quantize to the same frame')
        writes.add((f, path))
        events.append({'event_id': eid, 'frame': f, 'at_ms': ms, 'state_path': path, 'value': value,
                       'target_ids': expected, 'source_refs': list(p['source_refs']), 'reasoning_refs': list(p['reasoning_refs'])})

    cues = _items(raw.get('narration_cues', []), MAX_CUES, 'narration cues')
    narration, assets = _narration(cfg, cues, raw, elems, fps, duration_ms, targets)
    if not states and not narration:
        fail('FRAME_RUNTIME_EMPTY', 'extension declares no implemented consumer')
    if not cues and any(k in cfg for k in ('narration_revision', 'narration_texts', 'audio_assets', 'audio_segments', 'caption_target_id')):
        fail('FRAME_RUNTIME_UNUSED_NARRATION', 'narration metadata without cues is not consumed')
    result = {'schema_version': SCHEMA, 'input_identity': digest(raw), 'fps': fps, 'frame_count': frames,
              'initial_state': dict(sorted(states.items())), 'state_lineage': deepcopy(lineage),
              'bindings': sorted(bindings, key=lambda b: b['binding_id']),
              'events': sorted(events, key=lambda e: (e['frame'], e['event_id'])),
              'narration': narration, 'audio_assets': assets, 'caption_target_id': cfg.get('caption_target_id'),
              'quantization': 'CEIL_BOTH_BOUNDARIES_HALF_OPEN_NEVER_EARLY',
              'speech_text_alignment': 'NOT_VERIFIED', 'rights_verification': 'DECLARED_NOT_INDEPENDENTLY_VERIFIED',
              'accepted': False}
    result['plan_sha256'] = digest(result)
    return result


def _narration(cfg, cues, raw, elems, fps, duration_ms, binding_targets):
    if not cues:
        return [], []
    required = {'narration_revision', 'narration_texts', 'audio_assets', 'audio_segments', 'caption_target_id'}
    if not required <= set(cfg):
        fail('FRAME_RUNTIME_NARRATION_CONTRACT', 'narration needs source text, audio assets/segments and an existing caption target')
    revision = integer(cfg['narration_revision'], 1, 2**31 - 1, 'narration revision')
    texts = cfg['narration_texts']
    if not isinstance(texts, dict) or len(texts) > MAX_CUES:
        fail('FRAME_RUNTIME_NARRATION_TEXTS', 'bounded transcript registry required')
    caption = ident(cfg['caption_target_id'], 'caption target')
    if caption not in elems or elems[caption]['element_type'] != 'text':
        fail('FRAME_RUNTIME_CAPTION_TARGET', 'an explicit text element with a layout box is required')
    if any(b[0] == caption for b in binding_targets) or any(t['element_id'] == caption for t in raw.get('tracks', [])):
        fail('FRAME_RUNTIME_CAPTION_CONFLICT', 'caption target cannot have a competing state/animation writer')
    asset_by = {}
    for a in _items(cfg['audio_assets'], MAX_CUES, 'audio assets'):
        keys = {'asset_id', 'public_path', 'sha256', 'byte_length', 'sample_rate', 'channels', 'sample_width',
                'frame_count', 'rights_ref', 'source_refs', 'reasoning_refs'}
        fields(a, keys, keys, 'audio asset'); aid = ident(a['asset_id'], 'asset id')
        if aid in asset_by:
            fail('FRAME_RUNTIME_ASSET_DUPLICATE', aid)
        if not isinstance(a['sha256'], str) or not _SHA.fullmatch(a['sha256']):
            fail('FRAME_RUNTIME_ASSET_HASH', 'SHA-256 required')
        # Canonical content-addressed path has no URI, escapes, query string, symlink or alternative spelling.
        if a['public_path'] != 'narration/' + a['sha256'] + '.wav':
            fail('FRAME_RUNTIME_ASSET_PATH', 'use content-addressed public-relative PCM WAV paths')
        integer(a['byte_length'], 44, 32 * 1024 * 1024, 'WAV bytes')
        integer(a['sample_rate'], 8000, 96000, 'sample rate')
        integer(a['channels'], 1, 2, 'channels')
        if a['sample_width'] != 2 or type(a['sample_width']) is not int:
            fail('FRAME_RUNTIME_PCM_FORMAT', 'only signed 16-bit PCM WAV is supported')
        integer(a['frame_count'], 1, a['sample_rate'] * 3600, 'sample frame count')
        text(a['rights_ref'], 'rights reference'); refs(a, raw, aid)
        asset_by[aid] = deepcopy(a)
    if sum(a['byte_length'] for a in asset_by.values()) > 64 * 1024 * 1024:
        fail('FRAME_RUNTIME_ASSET_BUDGET', 'total narration assets exceed the 64 MiB workload budget')
    segments = {}
    for seg in _items(cfg['audio_segments'], MAX_CUES, 'audio segments'):
        keys = {'cue_id', 'asset_id', 'trim_before_frames', 'volume', 'transcript_sha256'}
        fields(seg, keys, keys, 'audio segment')
        cid = ident(seg['cue_id'], 'segment cue id')
        if cid in segments:
            fail('FRAME_RUNTIME_SEGMENT_DUPLICATE', cid)
        if seg['asset_id'] not in asset_by:
            fail('FRAME_RUNTIME_ASSET_MISSING', cid)
        integer(seg['trim_before_frames'], 0, fps * 3600, 'trim')
        number(seg['volume'], 0.000001, 1, 'narration gain')
        segments[cid] = seg
    used_texts, used_assets, ids, result = set(), set(), set(), []
    for c in cues:
        keys = {'cue_id', 'start_ms', 'end_ms', 'text_ref', 'narration_revision', 'target_ids'}
        fields(c, keys, keys, 'narration cue'); cid = ident(c['cue_id'], 'cue id')
        if cid in ids:
            fail('FRAME_RUNTIME_CUE_DUPLICATE', cid)
        ids.add(cid)
        if type(c['narration_revision']) is not int or c['narration_revision'] != revision:
            fail('FRAME_RUNTIME_NARRATION_STALE', cid)
        if not isinstance(c['target_ids'], list) or not c['target_ids'] or len(set(c['target_ids'])) != len(c['target_ids']) or not set(c['target_ids']) <= set(elems):
            fail('FRAME_RUNTIME_CUE_TARGETS', 'narration targets must reference existing elements')
        for target_id in c['target_ids']:
            ident(target_id, 'cue target')
        start = integer(c['start_ms'], 0, duration_ms - 1, 'cue start'); end = integer(c['end_ms'], start + 1, duration_ms, 'cue end')
        fs, fe = frame_at(start, fps), frame_at(end, fps)
        if fe <= fs:
            fail('FRAME_RUNTIME_CUE_COLLAPSED', 'cue has no rendered frame')
        ref = c['text_ref']
        if ref not in texts or cid not in segments:
            fail('FRAME_RUNTIME_CUE_UNBOUND', 'missing transcript or exactly matched segment')
        tr = fields(texts[ref], {'text', 'source_refs', 'reasoning_refs'}, {'text', 'source_refs', 'reasoning_refs'}, 'transcript')
        value = text(tr['text'], 'transcript'); refs(tr, raw, ref)
        seg = segments[cid]; a = asset_by[seg['asset_id']]
        import hashlib
        if seg['transcript_sha256'] != hashlib.sha256(value.encode('utf-8')).hexdigest():
            fail('FRAME_RUNTIME_TRANSCRIPT_HASH', 'segment transcript identity differs; speech alignment is still not proven')
        if (seg['trim_before_frames'] + fe - fs) * a['sample_rate'] > a['frame_count'] * fps:
            fail('FRAME_RUNTIME_AUDIO_TOO_SHORT', 'declared PCM duration does not cover the entire quantized cue')
        used_texts.add(ref); used_assets.add(a['asset_id'])
        result.append({'cue_id': cid, 'start_frame': fs, 'end_frame': fe, 'start_ms': start, 'end_ms': end,
                       'text_ref': ref, 'text': value, 'narration_revision': revision, 'target_ids': sorted(c['target_ids']),
                       'asset_id': a['asset_id'], 'public_path': a['public_path'], 'trim_before_frames': seg['trim_before_frames'],
                       'volume': seg['volume'], 'source_refs': list(tr['source_refs']), 'reasoning_refs': list(tr['reasoning_refs'])})
    result.sort(key=lambda c: (c['start_frame'], c['cue_id']))
    if set(segments) != ids or used_assets != set(asset_by) or used_texts != set(texts):
        fail('FRAME_RUNTIME_NARRATION_COVERAGE', 'orphan assets, segments or transcripts are not silently discarded')
    if len({a['public_path'] for a in asset_by.values()}) != len(asset_by):
        fail('FRAME_RUNTIME_ASSET_ALIAS', 'duplicate bytes must reuse a single asset identity')
    for a, b in zip(result, result[1:]):
        if a['end_frame'] > b['start_frame']:
            fail('FRAME_RUNTIME_NARRATION_OVERLAP', 'single-voice contract does not mix concurrent narration')
    if elems[caption]['props'].get('text') != result[0]['text']:
        fail('FRAME_RUNTIME_CAPTION_INITIAL', 'caption source element must preserve the first transcript literally')
    return result, sorted(asset_by.values(), key=lambda a: a['asset_id'])
