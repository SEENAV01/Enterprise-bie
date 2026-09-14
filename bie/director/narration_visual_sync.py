"""BIE-DIR-SYNC-001: narration-to-visual intent."""
from dataclasses import dataclass
from bie.scene_ir.contracts import CORE_ELEMENT_KINDS
from .sync_contract import (IntentBinding, SyncCue, SyncIndex, unique_inputs,
    parameters, finish_plan, same_plan, SyncIssue, SyncPlan)


@dataclass(frozen=True)
class VisualIntent:
    binding: IntentBinding
    kind: str
    lead_ms: int = 0
    tail_ms: int = 0


def sync_visual_intents(context, intents, policy_version="bie-dir-visual-sync/1.0.0"):
    index = SyncIndex(context)
    rows = unique_inputs(intents, VisualIntent)
    cues, by_target = [], {}
    for row in rows:
        if row.kind not in CORE_ELEMENT_KINDS:
            raise ValueError("unsupported Scene IR element kind")
        window = index.resolve(row.binding,row.lead_ms,row.tail_ms)
        key = (window.scene_id,row.binding.target_id)
        if key in by_target and by_target[key] != row.kind:
            raise ValueError("one visual target cannot change element kind")
        by_target[key] = row.kind
        cues.append(SyncCue(row.binding,row.kind,window,parameters(visibility="VISIBLE_DURING_WINDOW")))
    issues=[]
    for i,left in enumerate(cues):
        for right in cues[i+1:]:
            if (left.window.scene_id,left.binding.target_id)==(right.window.scene_id,right.binding.target_id):
                if max(left.window.start_ms,right.window.start_ms)<min(left.window.end_ms,right.window.end_ms):
                    issues.append(SyncIssue("OVERLAPPING_VISIBILITY_REQUESTS",right.binding.intent_id,
                        "Use one explicit visibility window for a shared target, or nonoverlapping windows.","DIR_SYNC_VISUAL"))
    return finish_plan(index,"BIE-DIR-SYNC-001",policy_version,rows,(),tuple(cues),issues)


def validate_visual_sync(context, plan):
    if not isinstance(plan,SyncPlan) or plan.task_id != "BIE-DIR-SYNC-001":
        raise ValueError("expected visual sync plan")
    return same_plan(plan,sync_visual_intents(context,plan.inputs,plan.policy_version))
