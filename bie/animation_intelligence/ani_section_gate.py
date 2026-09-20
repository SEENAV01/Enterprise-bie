from dataclasses import dataclass

class AniSectionGateError(ValueError): pass

@dataclass(frozen=True)
class AniSectionEvidence:
    regression_passed:bool
    original_tasks_implemented:int
    hardening_tasks_implemented:int
    sceneir_handoff_passed:bool
    actual_e2e_passed:bool
    realbook_harness_passed:bool
    benchmark_passed:bool
    mutation_gate_passed:bool
    empirical_render_evidence:bool
    realbook_acceptance_evidence:bool

@dataclass(frozen=True)
class AniSectionGateResult:
    implementation_status:str
    acceptance_status:str
    blockers:tuple[str,...]
    acceptance_blockers:tuple[str,...]
    can_move_to_scene_ir:bool
    review_required:bool=True
    accepted:bool=False

def evaluate_ani_section_gate(e):
    blockers=[]
    if not e.regression_passed:blockers.append("regression_failed")
    if e.original_tasks_implemented!=38:blockers.append("original_tasks_incomplete")
    if e.hardening_tasks_implemented!=20:blockers.append("hardening_tasks_incomplete")
    if not e.sceneir_handoff_passed:blockers.append("sceneir_handoff_failed")
    if not e.actual_e2e_passed:blockers.append("actual_e2e_failed")
    if not e.realbook_harness_passed:blockers.append("realbook_harness_failed")
    if not e.benchmark_passed:blockers.append("benchmark_failed")
    if not e.mutation_gate_passed:blockers.append("mutation_gate_failed")
    implementation_status="IMPLEMENTATION_SCOPE_COMPLETE" if not blockers else "IMPLEMENTED_WITH_GAPS"
    acceptance_blockers=[]
    if not e.empirical_render_evidence:acceptance_blockers.append("empirical_render_evidence_missing")
    if not e.realbook_acceptance_evidence:acceptance_blockers.append("realbook_acceptance_evidence_missing")
    acceptance_status="ACCEPTED" if not blockers and not acceptance_blockers else "ACCEPTANCE_BLOCKED"
    return AniSectionGateResult(
        implementation_status,acceptance_status,tuple(blockers),tuple(acceptance_blockers),
        not blockers,True,acceptance_status=="ACCEPTED"
    )
