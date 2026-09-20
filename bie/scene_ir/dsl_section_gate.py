from dataclasses import dataclass
@dataclass(frozen=True)
class DSLSectionEvidence:
    regression_passed:bool;original_tasks_implemented:int;hardening_tasks_implemented:int;ani_adoption_passed:bool;dsl_gate_passed:bool;compiler_preflight_passed:bool;actual_e2e_passed:bool;realbook_harness_passed:bool;benchmark_passed:bool;mutation_gate_passed:bool;empirical_compile_evidence:bool;empirical_render_evidence:bool;realbook_acceptance_evidence:bool
@dataclass(frozen=True)
class DSLSectionGate:
    implementation_status:str;acceptance_status:str;implementation_blockers:tuple[str,...];acceptance_blockers:tuple[str,...];can_move_to_comp:bool;accepted:bool=False
def evaluate_dsl_section_gate(e):
    impl=[]
    if not e.regression_passed:impl.append("regression_not_passed")
    if e.original_tasks_implemented<51:impl.append("original_tasks_incomplete")
    if e.hardening_tasks_implemented<20:impl.append("hardening_incomplete")
    for ok,name in ((e.ani_adoption_passed,"ani_adoption"),(e.dsl_gate_passed,"dsl_gate"),(e.compiler_preflight_passed,"compiler_preflight"),(e.actual_e2e_passed,"actual_e2e"),(e.realbook_harness_passed,"realbook_harness"),(e.benchmark_passed,"benchmark"),(e.mutation_gate_passed,"mutation_gate")):
        if not ok:impl.append(name+"_not_passed")
    acc=[]
    if not e.empirical_compile_evidence:acc.append("empirical_compile_evidence_missing")
    if not e.empirical_render_evidence:acc.append("empirical_render_evidence_missing")
    if not e.realbook_acceptance_evidence:acc.append("realbook_acceptance_evidence_missing")
    ist="IMPLEMENTATION_SCOPE_COMPLETE" if not impl else "IMPLEMENTED_WITH_GAPS"
    ast="ACCEPTANCE_BLOCKED" if acc or impl else "ACCEPTED"
    return DSLSectionGate(ist,ast,tuple(impl),tuple(acc),not impl,not impl and not acc)
