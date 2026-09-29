"""Checked projection to the pinned native DIR contracts, never an acceptance flag.

The native builders sort records by ID. Preserve actual route/timeline ordering
in DirectorRequest; native sorted record order is NOT a playback schedule.
"""
from dataclasses import dataclass
from bie.director.lesson_architecture_contract import (
    LessonSceneIntent, build_lesson_architecture, validate_lesson_architecture)
from bie.director.script_plan import ScriptSegment, build_script_plan, validate_script_plan
from ..release_v2.contracts import ContractError
from .models import DirectorRequest
from .metrics import merged_text


@dataclass(frozen=True, slots=True)
class NativeProjection:
    architecture: object
    script: object
    requires_review: bool = True


def to_native(request, policy_id='director-qa-v1'):
    if type(request) is not DirectorRequest: raise ContractError('DIR_NATIVE_REQUEST_TYPE')
    claims = {c.claim_id: c for c in request.source.claims}
    scenes = {s.scene_id: s for s in request.scenes}; script = []; intents = []
    spoken = {x.beat_id: x for x in request.spoken_forms}
    for s in request.scenes:
        ids = tuple(sorted({cid for b in request.beats if b.scene_id == s.scene_id for cid in b.claim_ids}))
        if not ids or not set(ids) <= set(claims): raise ContractError('DIR_NATIVE_SCENE_EVIDENCE')
        intents.append(LessonSceneIntent(s.scene_id, s.purpose, s.objective_ids, ids, s.parent_scene_ids, True))
    for b in request.beats:
        if b.channel == 'pause': continue
        if b.scene_id not in scenes or not set(b.claim_ids) <= set(claims): raise ContractError('DIR_NATIVE_BEAT_REFERENCE')
        form = spoken.get(b.beat_id)
        evidence = tuple(sorted(set(b.claim_ids + (form.claim_ids if form else ()))))
        script.append(ScriptSegment(b.beat_id, b.scene_id, b.role, form.text if form else merged_text(claims, b.claim_ids),
                                    evidence, b.objective_ids or scenes[b.scene_id].objective_ids))
    try:
        architecture = build_lesson_architecture(request.lesson_id, request.lesson_id, tuple(intents),
                tuple(sorted({o for s in request.scenes for o in s.objective_ids})),
                tuple(sorted(s.source_id for s in request.source.sources)), policy_id)
        plan = build_script_plan(request.lesson_id, tuple(script), 'reviewed-per-beat-voice-map')
        validate_lesson_architecture(architecture); validate_script_plan(plan)
    except (ValueError, TypeError, RecursionError) as exc:
        raise ContractError('DIR_NATIVE_CONTRACT_REJECTED') from exc
    return NativeProjection(architecture, plan)
