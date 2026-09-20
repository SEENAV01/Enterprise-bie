"""H10 finite frame-conformance diagnostics over actual generated TypeScript.

This controlled diagnostic executes the retained, explicitly labelled API-double
bridge. It is NOT React/Remotion, an OS sandbox, or render-release authorization.
The independent Python frame oracle detects dropped controls, wrong nesting and
frame-dependent disagreement, including reverse seeks.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import json
import math
import tempfile

from .artifact_hashing import canonical_json
from .frame_runtime_contract import plan_frame_runtime
from .frame_state_consumer import runtime_at
from .qa_common import CompilerQAError, digest
from .render_process import run_bounded_process

MAX_EXECUTIONS = 2000
SCOPE = 'GENERATED_TYPESCRIPT_WITH_EXPLICIT_REACT_REMOTION_API_DOUBLES'


def _walk(node, ancestors=()):
    if isinstance(node, list):
        for child in node:
            yield from _walk(child, ancestors)
    elif isinstance(node, dict):
        yield node, ancestors
        yield from _walk(node.get('children', []), ancestors + (node,))


def _same(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    return a == b


def inspect_composed_trees(plan, data, frames):
    """Inspect diagnostic observations; this receipt never authorizes rendering."""
    if (not isinstance(data, dict) or data.get('real_react') is not False
            or data.get('real_remotion') is not False or data.get('audio_played') is not False
            or data.get('execution_kind') != 'REAL_TS_WHOLE_SCENE_WITH_EXPLICIT_REACT_REMOTION_TEST_DOUBLES'):
        raise CompilerQAError('COMPOSITION_DIAGNOSTIC_SCOPE_MISMATCH')
    trees = data.get('trees')
    if (not isinstance(trees, list) or any(not isinstance(row, dict) or not {'frame','tree','state'} <= set(row) for row in trees)
            or [row.get('frame') for row in trees] != list(frames)):
        raise CompilerQAError('COMPOSITION_FRAME_COVERAGE_MISMATCH')
    findings, records, replay = [], [], {}
    def note(code, frame, target):
        findings.append({'code':code, 'frame':frame, 'target_id':target})
    for row in trees:
        frame = row['frame']; expected = runtime_at(plan, frame)
        if not _same(row.get('state'), expected):
            note('COMPOSITION_RUNTIME_ORACLE_MISMATCH', frame, '*')
        tree_identity = digest(row['tree'])
        if frame in replay and replay[frame] != tree_identity:
            note('COMPOSITION_REVERSE_SEEK_MISMATCH', frame, '*')
        replay[frame] = tree_identity
        walked = list(_walk(row['tree']))
        for comp in plan.get('state_motion_compositions', []):
            eid = comp['target_id']; controls = [(n, ancestors) for n, ancestors in walked
                if n.get('props', {}).get('data-bie-runtime-target') == eid
                and n.get('props', {}).get('data-bie-runtime-mode') == 'controls']
            if len(controls) != 1:
                note('COMPOSITION_CONTROL_MISSING_OR_DUPLICATE', frame, eid); continue
            control, ancestors = controls[0]; style = control.get('props', {}).get('style', {})
            bound = expected['targets'].get(eid, {})
            opacity = bound.get('opacity', 1)
            if type(style.get('opacity')) not in (int, float) or not math.isclose(style['opacity'], opacity, abs_tol=1e-12):
                note('COMPOSITION_OPACITY_MISMATCH', frame, eid)
            visibility = 'hidden' if bound.get('visible') is False else 'visible'
            if style.get('visibility') != visibility:
                note('COMPOSITION_VISIBILITY_MISMATCH', frame, eid)
            track_records = []
            for tid in comp['track_ids']:
                owners = [(n, anc) for n, anc in walked if n.get('props', {}).get('data-bie-track-id') == tid]
                if len(owners) != 1:
                    note('COMPOSITION_TRACK_MISSING_OR_DUPLICATE', frame, eid)
                elif (tid in comp['content_track_ids'] and not any(a is control for a in owners[0][1])) or (tid in comp['outer_geometry_track_ids'] and not any(a is owners[0][0] for a in ancestors)):
                    note('COMPOSITION_CONTROL_PLACEMENT_MISMATCH', frame, eid)
                else:
                    track_records.append({'track_id':tid,'style':owners[0][0].get('props', {}).get('style', {})})
            records.append({'frame':frame,'element_id':eid,'visibility':style.get('visibility'),
                            'opacity':style.get('opacity'),'tracks':track_records})
    return {'schema_version':'bie.comp-composition-conformance.v1','scope':SCOPE,
            'executions':len(trees),'unique_frames':len(replay),'records':records,'findings':findings,
            'passed':not findings,'actual_render_verified':False,'release_authorized':False,'accepted':False}


def verify_composition(result, target, *, reverse_seek=True):
    if not result.receipt.source_gate_passed:
        raise CompilerQAError('COMPOSITION_SOURCE_GATE_REQUIRED')
    plan = plan_frame_runtime(result.effective_document, target)
    if plan is None or not plan.get('state_motion_compositions'):
        raise CompilerQAError('COMPOSITION_CONTRACT_REQUIRED')
    count = plan['frame_count']
    frames = list(range(count))
    if reverse_seek:
        frames = list(reversed(frames)) + frames
    if len(frames) > MAX_EXECUTIONS:
        raise CompilerQAError('COMPOSITION_EXECUTION_BUDGET: never sample into a pass')
    for item in result.codegen.files:
        if sha256(item.content.encode('utf-8')).hexdigest() != item.sha256:
            raise CompilerQAError('COMPOSITION_SOURCE_BYTES_MISMATCH')
    req = {'files':{f.path:f.content for f in result.codegen.files},'frames':frames,
           'fps':target.fps,'width':target.width,'height':target.height}
    bridge = Path(__file__).parent/'qa_support/frame_runtime_bridge.cjs'
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'request.json'; path.write_bytes(canonical_json(req))
        run = run_bounded_process(['node',str(bridge),str(path)],cwd=td,timeout_s=90,max_output_bytes=64*1024*1024)
    if not run.process.passed:
        raise CompilerQAError('COMPOSITION_EXECUTION_FAILED: '+run.outcome+': '+run.process.stderr[:600])
    data = json.loads(run.process.stdout)
    report = inspect_composed_trees(plan, data, frames)
    report.update(scene_identity=digest(result.effective_document),manifest_sha256=result.codegen.manifest_sha256,
                  bridge_sha256=sha256(bridge.read_bytes()).hexdigest(),typescript_version=data['typescript_version'],
                  runtime_plan_sha256=plan['plan_sha256'],output_sha256=sha256(run.process.stdout.encode()).hexdigest())
    return report
