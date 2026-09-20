"""H5-001. Versioned, bounded consumers for the existing camera/morph/trace actions.

These contracts do not infer a camera, invent a derivation, or reinterpret graph
coordinates. They consume decisions with explicit source and reasoning lineage.
Frame endpoints share H2's half-open interval and final-included-frame policy.
"""
from __future__ import annotations
from collections.abc import Mapping
from copy import deepcopy
import math
from .animation_compiler_common import normalize_track, AnimationCompilerError
from .hardening_contracts import finite_number

SCHEMA = 'bie.comp-specialized-motion.v1'
ACTIONS = frozenset({'camera', 'morph', 'trace'})


def fail(code, message):
    raise AnimationCompilerError(code + ': ' + message)


def is_specialized(track):
    params = track.get('parameters', {}) if isinstance(track, Mapping) else getattr(track, 'parameters', {})
    return isinstance(params, Mapping) and params.get('schema_version') == SCHEMA


def _number(value, name, low=-1e7, high=1e7):
    try:
        v = finite_number(value, name)
    except ValueError as exc:
        fail('SPECIALIZED_NUMBER_INVALID', str(exc))
    if not low <= v <= high:
        fail('SPECIALIZED_NUMBER_INVALID', name + ' outside supported bounds')
    return v


def _text(value, name, maximum=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or '\x00' in value:
        fail('SPECIALIZED_TEXT_INVALID', name + ' must be bounded nonblank text')
    return value


def _fields(value, required, optional=()):
    if not isinstance(value, Mapping) or not set(required) <= set(value) or set(value) - set(required) - set(optional):
        fail('SPECIALIZED_PARAMETER_UNCONSUMED', 'fields must match ' + ','.join(sorted(required)))


def _refs(values, allowed, name):
    if not isinstance(values, (list, tuple)) or not values or len(values) > 128:
        fail('SPECIALIZED_PROVENANCE_UNBOUND', name + ' needs bounded nonempty references')
    if any(not isinstance(v, str) or not v.strip() for v in values) or len(set(values)) != len(values) or not set(values) <= set(allowed):
        fail('SPECIALIZED_PROVENANCE_UNBOUND', name + ' must refer to declared lineage')
    return list(values)


def specialized_contract(track):
    from .animation_behavior import MotionContract
    tid, eid, action, start, end, p, source, reason = normalize_track(track)
    if action not in ACTIONS or p.get('schema_version') != SCHEMA:
        fail('SPECIALIZED_SCHEMA_REQUIRED', 'unsupported specialized action/version')
    if end > 3600000:
        fail('ANIMATION_TIME_BOUNDS', 'track interval exceeds one hour')
    if len(set(source)) != len(source) or len(set(reason)) != len(reason):
        fail('SPECIALIZED_PROVENANCE_UNBOUND', 'duplicate track provenance')
    easing = p.get('easing', 'linear')
    if easing not in ('linear', 'smoothstep'):
        fail('ANIMATION_EASING_UNSUPPORTED', 'linear or smoothstep required')
    base = {'schema_version', 'easing'}
    if action == 'camera':
        _fields(p, {'schema_version', 'projection', 'coordinate_space', 'viewport', 'from', 'to'}, {'easing'})
        if p['projection'] != 'orthographic-2d' or p['coordinate_space'] != 'element-pixels':
            fail('CAMERA_SPACE_UNSUPPORTED', 'explicit 2D orthographic element-pixel coordinates required')
        _fields(p['viewport'], {'width', 'height'})
        viewport = {k: _number(p['viewport'][k], k, 1, 8192) for k in ('width', 'height')}
        poses = {}
        for side in ('from', 'to'):
            _fields(p[side], {'focus_x', 'focus_y', 'zoom'})
            poses[side] = {'focus_x': _number(p[side]['focus_x'], 'focus_x', 0, viewport['width']),
                           'focus_y': _number(p[side]['focus_y'], 'focus_y', 0, viewport['height']),
                           'zoom': _number(p[side]['zoom'], 'zoom', .1, 10)}
        if poses['from'] == poses['to']:
            fail('ANIMATION_NO_VISUAL_CHANGE', 'camera poses are identical')
        parameters = {'schema_version': SCHEMA, 'projection': p['projection'],
                      'coordinate_space': p['coordinate_space'], 'viewport': viewport, **poses}
        owned = ('scale', 'translate')
    elif action == 'morph':
        _fields(p, {'schema_version', 'mode', 'states', 'transition_fraction'}, {'easing'})
        if p['mode'] != 'typeset-state-crossfade':
            fail('EQUATION_MORPH_MODE_UNSUPPORTED', 'symbol mapping is not implemented; explicit typeset-state-crossfade required')
        fraction = _number(p['transition_fraction'], 'transition_fraction', .1, .5)
        states = p['states']
        if not isinstance(states, (list, tuple)) or not 2 <= len(states) <= 12:
            fail('EQUATION_STATES_INVALID', '2..12 explicit states required')
        checked = []
        for row in states:
            _fields(row, {'expression', 'alt', 'source_refs', 'reasoning_refs'})
            s = {'expression': _text(row['expression'], 'expression', 12000),
                 'alt': _text(row['alt'], 'state alt', 12000),
                 'source_refs': _refs(row['source_refs'], source, 'state source_refs'),
                 'reasoning_refs': _refs(row['reasoning_refs'], reason, 'state reasoning_refs')}
            if checked and s['expression'] == checked[-1]['expression']:
                fail('EQUATION_STATES_INVALID', 'adjacent equation states must differ')
            checked.append(s)
        parameters = {'schema_version': SCHEMA, 'mode': p['mode'], 'states': checked,
                      'transition_fraction': fraction}
        owned = ('content',)
    else:
        _fields(p, {'schema_version', 'series_id', 'progress_model', 'head_marker'}, {'easing'})
        if p['progress_model'] != 'screen-arc-length' or type(p['head_marker']) is not bool:
            fail('TRACE_PROGRESS_MODEL_UNSUPPORTED', 'explicit screen-arc-length and boolean head_marker required')
        parameters = {'schema_version': SCHEMA, 'series_id': _text(p['series_id'], 'series_id', 128),
                      'progress_model': p['progress_model'], 'head_marker': p['head_marker']}
        owned = ('content',)
    return MotionContract(tid, eid, action, start, end, easing, parameters, owned)


def progress_at(contract, frame, fps):
    from .animation_behavior import frame_window
    if type(frame) is not int or frame < 0:
        fail('ANIMATION_FRAME_INVALID', 'frame must be a nonnegative integer')
    a, b = frame_window(contract, fps)
    u = max(0., min(1., (frame-a)/(b-a)))
    return u*u*(3-2*u) if contract.easing == 'smoothstep' else u


def camera_state(contract, frame, fps):
    u = progress_at(contract, frame, fps)
    p = contract.parameters
    pose = {k: p['from'][k] + (p['to'][k]-p['from'][k])*u for k in p['from']}
    # World position at focus maps to the center, i.e. inverse camera movement.
    return {'scale': pose['zoom'],
            'translate_x': (p['viewport']['width']/2-pose['focus_x'])*pose['zoom'],
            'translate_y': (p['viewport']['height']/2-pose['focus_y'])*pose['zoom']}


def equation_state(contract, frame, fps):
    p = contract.parameters
    location = progress_at(contract, frame, fps)*(len(p['states'])-1)
    lo = min(len(p['states'])-1, math.floor(location))
    hi = min(len(p['states'])-1, lo+1)
    alpha = max(0., min(1., (location-lo-(1-p['transition_fraction']))/p['transition_fraction']))
    if lo == hi: alpha = 0.
    return {'lower': lo, 'upper': hi, 'upper_opacity': alpha, 'lower_opacity': 1-alpha}


def graph_contract(element):
    """Finite signed-data polyline plot. No clipping, rescaling inference or loss of units."""
    if element.get('element_type') != 'graph':
        fail('TRACE_TARGET_TYPE_MISMATCH', 'trace consumes a graph element')
    p = element.get('props', {})
    _fields(p, {'series', 'x_domain', 'y_domain', 'x_label', 'y_label', 'x_unit', 'y_unit'})
    domains = {}
    for axis in ('x', 'y'):
        d = p[axis+'_domain']
        if not isinstance(d, (list, tuple)) or len(d) != 2:
            fail('TRACE_DOMAIN_INVALID', 'two increasing finite endpoints required')
        a, b = (_number(v, axis+' endpoint', -1e12, 1e12) for v in d)
        if b-a < max(1e-12, max(abs(a), abs(b))*1e-12):
            fail('TRACE_DOMAIN_INVALID', 'domain is non-increasing or numerically unresolved')
        domains[axis] = [a, b]
    labels = {k: _text(p[k], k, 200) for k in ('x_label', 'y_label', 'x_unit', 'y_unit')}
    if not isinstance(p['series'], (list, tuple)) or not 1 <= len(p['series']) <= 8:
        fail('TRACE_SERIES_INVALID', '1..8 explicit polylines required')
    checked, seen = [], set()
    for s in p['series']:
        _fields(s, {'series_id', 'label', 'points'})
        sid = _text(s['series_id'], 'series_id', 128)
        if sid in seen: fail('TRACE_SERIES_INVALID', 'duplicate series_id')
        seen.add(sid)
        label = _text(s['label'], 'series label', 200)
        if not isinstance(s['points'], (list, tuple)) or not 2 <= len(s['points']) <= 2048:
            fail('TRACE_POINTS_INVALID', '2..2048 source points required')
        pts, pixels = [], []
        for row in s['points']:
            if not isinstance(row, (list, tuple)) or len(row) != 2:
                fail('TRACE_POINTS_INVALID', 'exactly x,y required')
            xy = [_number(v, 'point', -1e12, 1e12) for v in row]
            if not all(domains[a][0] <= xy[i] <= domains[a][1] for i, a in enumerate(('x', 'y'))):
                fail('TRACE_POINT_OUTSIDE_DOMAIN', 'source data cannot be clipped or silently normalized')
            screen = [48+(xy[0]-domains['x'][0])/(domains['x'][1]-domains['x'][0])*320,
                      184-(xy[1]-domains['y'][0])/(domains['y'][1]-domains['y'][0])*150]
            if pixels and math.dist(pixels[-1], screen) < 1e-6:
                fail('TRACE_POINTS_UNRESOLVED', 'adjacent vertices collapse in the declared plot')
            pts.append(xy); pixels.append(screen)
        lengths = [math.dist(a, b) for a, b in zip(pixels, pixels[1:])]
        checked.append({'series_id': sid, 'label': label, 'points': pts, 'pixels': pixels,
                        'lengths': lengths, 'total_length': sum(lengths)})
    return {'domains': domains, **labels, 'series': checked, 'viewbox': [0, 0, 416, 244+16*len(checked)],
            'plot_bounds': [48, 34, 368, 184], 'projection': 'linear-data-to-svg', 'accepted': False}


def trace_state(contract, graph, frame, fps):
    u = progress_at(contract, frame, fps)
    s = next((s for s in graph['series'] if s['series_id'] == contract.parameters['series_id']), None)
    if s is None: fail('TRACE_SERIES_MISSING', 'selected series_id not found')
    if u in (0., 1.):
        i = 0 if u == 0 else -1
        return {'progress': u, 'head': list(s['pixels'][i]), 'data': list(s['points'][i]), 'dash_offset': 1-u}
    distance, covered = u*s['total_length'], 0.
    for i, length in enumerate(s['lengths']):
        if distance <= covered+length or i == len(s['lengths'])-1:
            r = min(1., max(0., (distance-covered)/length))
            head = [s['pixels'][i][k]+(s['pixels'][i+1][k]-s['pixels'][i][k])*r for k in (0, 1)]
            data = [s['points'][i][k]+(s['points'][i+1][k]-s['points'][i][k])*r for k in (0, 1)]
            return {'progress': u, 'head': head, 'data': data, 'dash_offset': 1-u}
        covered += length
    fail('TRACE_SERIES_INVALID', 'empty path')


def validate_element_source(contract, element, source_refs, reasoning_refs):
    if not isinstance(element, Mapping) or element.get('element_id') != contract.element_id:
        fail('SPECIALIZED_TARGET_MISMATCH', 'contract does not bind this source element')
    _refs(source_refs, element.get('source_refs', []), 'track source_refs')
    _refs(reasoning_refs, element.get('reasoning_refs', []), 'track reasoning_refs')
    if contract.action == 'morph':
        p = element.get('props', {})
        if element.get('element_type') != 'equation' or p.get('format', 'latex') != 'latex':
            fail('EQUATION_MORPH_TARGET_UNSUPPORTED', 'bounded LaTeX equation target required')
        _fields(p, {'expression'}, {'format', 'side_conditions', 'renderer', 'font_size'})
        if p.get('renderer', 'mathtext-svg') != 'mathtext-svg':
            fail('EQUATION_RENDERER_UNSUPPORTED', 'the explicit bounded mathtext-svg renderer is required')
        if contract.parameters['states'][0]['expression'] != p.get('expression'):
            fail('EQUATION_INITIAL_STATE_MISMATCH', 'first step must equal the source equation')
        side = p.get('side_conditions', [])
        if not isinstance(side, (list, tuple)) or len(side)>32:
            fail('EQUATION_SIDE_CONDITIONS_INVALID', 'bounded explicit side conditions required')
        for v in side: _text(v, 'side condition', 1000)
    elif contract.action == 'trace':
        graph = graph_contract(element)
        if contract.parameters['series_id'] not in {s['series_id'] for s in graph['series']}:
            fail('TRACE_SERIES_MISSING', 'selected series not in source')
    return True


def validate_binding(contract, element, target, duration_ms, source_refs, reasoning_refs):
    from .animation_behavior import frame_window
    if element['element_id'] != contract.element_id:
        fail('SPECIALIZED_TARGET_MISMATCH', 'contract does not bind this element')
    validate_element_source(contract, element, source_refs, reasoning_refs)
    # New metadata must never introduce unbound cited facts or reasoning IDs.
    _refs(source_refs, element.get('source_refs', []), 'track source_refs')
    _refs(reasoning_refs, element.get('reasoning_refs', []), 'track reasoning_refs')
    a, b = frame_window(contract, target.fps)
    count = (duration_ms*target.fps+999)//1000
    if b >= count: fail('ANIMATION_EXCEEDS_SCENE', 'required final sample is outside scene')
    p = contract.parameters
    if contract.action == 'camera':
        box = element.get('normalized_box')
        if not isinstance(box, Mapping): fail('CAMERA_VIEWPORT_MISMATCH', 'explicit target box required')
        for axis in ('width', 'height'):
            if not math.isclose(p['viewport'][axis], box[axis]*getattr(target, axis), abs_tol=1e-6, rel_tol=0):
                fail('CAMERA_VIEWPORT_MISMATCH', 'viewport differs from actual element-pixel dimensions')
    elif contract.action == 'morph':
        e = element.get('props', {})
        if element.get('element_type') != 'equation' or e.get('format', 'latex') != 'latex':
            fail('EQUATION_MORPH_TARGET_UNSUPPORTED', 'bounded LaTeX equation target required')
        if p['states'][0]['expression'] != e.get('expression'):
            fail('EQUATION_INITIAL_STATE_MISMATCH', 'first step must equal source equation, not replace it silently')
        # A pure displayed sample of every state is required even under easing.
        pure = set()
        for f in range(a, b+1):
            state = equation_state(contract, f, target.fps)
            if state['upper_opacity'] < 1e-9: pure.add(state['lower'])
        if pure != set(range(len(p['states']))):
            fail('EQUATION_STATES_UNSAMPLED', 'each equation state needs a pure rendered sample')
    else:
        graph = graph_contract(element)
        if p['series_id'] not in {s['series_id'] for s in graph['series']}:
            fail('TRACE_SERIES_MISSING', 'selected source series does not exist')
    return {'track_id': contract.track_id, 'element_id': contract.element_id, 'action': contract.action,
            'source_refs': list(source_refs), 'reasoning_refs': list(reasoning_refs),
            'schema_version': SCHEMA, 'sample_start_frame': a, 'sample_end_frame': b,
            'symbolic_equivalence_verified': False, 'instructional_equivalence_verified': False,
            'real_remotion_verified': False, 'accepted': False}


def validate_specialized_bindings(raw, target):
    elements = {e['element_id']: e for e in raw['elements']}
    results = []
    for t in raw.get('tracks', []):
        if not is_specialized(t): continue
        c = specialized_contract(t)
        if c.element_id not in elements: fail('SPECIALIZED_TARGET_MISMATCH', 'unknown element')
        results.append(validate_binding(c, elements[c.element_id], target, raw['duration_ms'], t['source_refs'], t['reasoning_refs']))
    return results
