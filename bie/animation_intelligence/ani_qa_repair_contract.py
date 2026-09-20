from dataclasses import dataclass

class QARepairError(ValueError): pass

OWNER_ACTIONS={
 "SEM":{"change_action","change_target","repair_identity"},
 "ATTN":{"adjust_focus","reduce_competing_motion"},
 "DOMAIN":{"repair_domain_semantics","replace_unsupported_pattern"},
 "EASE":{"change_easing","change_duration","apply_reduced_motion"},
 "TIMELINE":{"shift_track","split_scene","extend_scene"},
 "CONTINUITY":{"authorize_change","restore_identity","restore_trajectory"},
 "QA":{"recompute_qa"},
}

@dataclass(frozen=True)
class RepairInstruction:
    repair_id:str
    qa_id:str
    track_ids:tuple[str,...]
    owner_stage:str
    action:str
    reason_code:str
    evidence_refs:tuple[str,...]
    expected_postcondition:str
    automatic:bool=False
    accepted:bool=False

def make_repair_instruction(repair_id,qa_id,track_ids,owner_stage,action,reason_code,
                            evidence_refs,expected_postcondition,automatic=False):
    if owner_stage not in OWNER_ACTIONS:
        raise QARepairError("unknown owner_stage")
    if action not in OWNER_ACTIONS[owner_stage]:
        raise QARepairError("action not allowed for owner_stage")
    if not track_ids or not evidence_refs or not expected_postcondition:
        raise QARepairError("repair traceability incomplete")
    if reason_code.startswith("empirical_") and automatic:
        raise QARepairError("empirical failures cannot be auto-repaired without verification")
    return RepairInstruction(repair_id,qa_id,tuple(track_ids),owner_stage,action,reason_code,
                             tuple(evidence_refs),expected_postcondition,bool(automatic),False)

def validate_repair_closure(instruction,postcondition_met,qa_status_after):
    if not postcondition_met:
        raise QARepairError("repair postcondition not met")
    if qa_status_after not in {"PASS","REVIEW"}:
        raise QARepairError("QA still blocked after repair")
    return True
