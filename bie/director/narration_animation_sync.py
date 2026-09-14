"""BIE-DIR-SYNC-002: narration-to-animation intent with causal ordering."""
from dataclasses import dataclass
from collections import deque
from .timing_contract import integer
from .sync_contract import (IntentBinding, SyncCue, SyncIndex, SyncIssue, unique_inputs,
    immutable_ids, parameters, finish_plan, require_target, SyncPlan, same_plan)
from .narration_visual_sync import validate_visual_sync

# Channels follow property ownership so incompatible motions cannot be hidden
# by caller-supplied channel names. Renderer-specific keyframes are deferred.
CHANNELS={"enter":"visibility","exit":"visibility","reveal":"visibility",
          "emphasize":"emphasis","trace":"path","path_follow":"path",
          "translate":"position","rotate":"rotation","scale":"scale",
          "opacity":"opacity","transform":"transform","simulation_state":"state"}
OWNERS={kind:{channel} for kind,channel in CHANNELS.items()}
OWNERS["path_follow"]={"path","position"}
OWNERS["transform"]={"position","rotation","scale","path"}


@dataclass(frozen=True)
class AnimationIntent:
    binding: IntentBinding
    visual_intent_id: str
    kind: str
    minimum_duration_ms: int = 1
    after_intent_ids: tuple[str, ...] = ()


def sync_animation_intents(context, visuals, intents, policy_version="bie-dir-animation-sync/1.0.0"):
    validate_visual_sync(context,visuals)
    index = SyncIndex(context)
    rows = unique_inputs(intents,AnimationIntent)
    by_visual={c.binding.intent_id:c for c in visuals.cues}
    by_row={r.binding.intent_id:r for r in rows}
    cues,issues=[],list(visuals.issues)
    for row in rows:
        if row.kind not in CHANNELS:
            raise ValueError("animation kind requires a supported property channel")
        integer(row.minimum_duration_ms,"minimum_duration_ms",1)
        immutable_ids(row.after_intent_ids,"animation dependencies",empty=True)
        if any(dep not in by_row or dep==row.binding.intent_id for dep in row.after_intent_ids):
            raise ValueError("unknown or self-referencing animation dependency")
        if row.visual_intent_id not in by_visual:
            raise ValueError("unknown visual intent")
        cue=SyncCue(row.binding,row.kind,index.resolve(row.binding),
                    parameters(channel=CHANNELS[row.kind],owned_properties=tuple(sorted(OWNERS[row.kind])),
                               after_intent_ids=row.after_intent_ids))
        issues.extend(require_target(cue,by_visual[row.visual_intent_id]))
        if cue.window.end_ms-cue.window.start_ms < row.minimum_duration_ms:
            issues.append(SyncIssue("ANIMATION_WINDOW_TOO_SHORT",row.binding.intent_id,
                "Narration interval is shorter than the required animation duration.","DIR_TIME"))
        cues.append(cue)
    # Iterative cycle checking also supports long narration dependency chains.
    pending={key:len(row.after_intent_ids) for key,row in by_row.items()}
    children={key:[] for key in by_row}
    for key,row in by_row.items():
        for dep in row.after_intent_ids: children[dep].append(key)
    ready=deque(key for key,count in pending.items() if count==0)
    completed=0
    while ready:
        key=ready.popleft(); completed+=1
        for child in children[key]:
            pending[child]-=1
            if pending[child]==0: ready.append(child)
    if completed!=len(by_row): raise ValueError("animation dependency cycle")
    by_cue={c.binding.intent_id:c for c in cues}
    for row in rows:
        cue=by_cue[row.binding.intent_id]
        for dep in row.after_intent_ids:
            other=by_cue[dep]
            if other.window.scene_id != cue.window.scene_id:
                raise ValueError("animation dependencies must be scene-local")
            if other.window.end_ms > cue.window.start_ms:
                issues.append(SyncIssue("DEPENDENCY_NOT_FINISHED",row.binding.intent_id,
                    f"Required predecessor {dep} has not ended at the requested start.","DIR_SYNC_ANIMATION"))
    for i,a in enumerate(cues):
        for b in cues[i+1:]:
            if (a.window.scene_id,a.binding.target_id)==(b.window.scene_id,b.binding.target_id):
                conflict=OWNERS[a.kind]&OWNERS[b.kind]
                if conflict and max(a.window.start_ms,b.window.start_ms)<min(a.window.end_ms,b.window.end_ms):
                    issues.append(SyncIssue("ANIMATION_PROPERTY_CONFLICT",b.binding.intent_id,
                        f"Overlapping property ownership with {a.binding.intent_id}.","DIR_SYNC_ANIMATION"))
    return finish_plan(index,"BIE-DIR-SYNC-002",policy_version,rows,(),tuple(cues),issues,
                       visuals.fingerprint(),visuals.review_reasons)


def validate_animation_sync(context, visuals, plan):
    if not isinstance(plan,SyncPlan) or plan.task_id!="BIE-DIR-SYNC-002":
        raise ValueError("expected animation sync plan")
    return same_plan(plan,sync_animation_intents(context,visuals,plan.inputs,plan.policy_version))
