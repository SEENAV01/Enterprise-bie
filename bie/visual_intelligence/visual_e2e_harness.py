from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Any
from .capability_handoff import assert_handoff_consumable
from .complexity_budget import assert_semantics_preserved
from .qa_trace_matrix import require_trace_pass
from .accessibility_integration import assert_accessible_for_handoff
from .asset_lifecycle import production_ready
from .replay_currentness import assert_current

class VisualE2EError(RuntimeError): pass

CANONICAL_STAGES=("DIR_ADOPT","REP","GRAM","LAYOUT","ASSET","TEXT","ACCESS","QA","HANDOFF","PERF")

@dataclass(frozen=True)
class StageEvidence:
    stage:str
    current:bool
    status:str
    evidence_id:str

@dataclass(frozen=True)
class VisualE2EReport:
    run_id:str
    completed_stages:tuple[str,...]
    blockers:tuple[str,...]
    passed:bool
    review_required:bool=True
    accepted:bool=False

def run_visual_e2e(*,run_id,stage_evidence,trace_audit,accessibility_result,asset_states,
                   handoff,complexity_decision,output_semantic_ids,replay_record,replay_vector,
                   input_fingerprint,replay_dependency_ids,raw_source_supplied=False):
    if raw_source_supplied: raise VisualE2EError("raw source cannot enter VIS E2E; canonical DIR handoff required")
    by={x.stage:x for x in stage_evidence}
    if set(by)!=set(CANONICAL_STAGES): raise VisualE2EError("E2E stage evidence incomplete")
    blockers=[]
    for s in CANONICAL_STAGES:
        ev=by[s]
        if not ev.current: blockers.append("stale_stage:"+s)
        if ev.status not in {"PASS","REVIEW"}: blockers.append("stage_blocked:"+s)
    try: require_trace_pass(trace_audit)
    except Exception: blockers.append("trace_gate_failed")
    try: assert_accessible_for_handoff(accessibility_result)
    except Exception: blockers.append("accessibility_gate_failed")
    if any(not production_ready(a) for a in asset_states): blockers.append("asset_lifecycle_gate_failed")
    try: assert_handoff_consumable(handoff)
    except Exception: blockers.append("handoff_gate_failed")
    try: assert_semantics_preserved(complexity_decision,output_semantic_ids)
    except Exception: blockers.append("complexity_semantic_loss")
    try: assert_current(replay_record,replay_vector,input_fingerprint,replay_dependency_ids)
    except Exception: blockers.append("replay_currentness_gate_failed")
    return VisualE2EReport(run_id,CANONICAL_STAGES,tuple(sorted(set(blockers))),not blockers,True,False)
