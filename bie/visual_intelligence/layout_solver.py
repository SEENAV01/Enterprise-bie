from __future__ import annotations
from dataclasses import dataclass
from .layout_contracts import LayoutValidationError
from .semantic_layout_constraints import evaluate_constraints
from .safe_area import enforce_safe_area
from .subtitle_safe_layout import enforce_subtitle_safe
from .collision_avoidance import avoid_collisions,detect_collisions

class LayoutSolverError(LayoutValidationError): pass

@dataclass(frozen=True)
class SolverReport:
    solved:bool
    iterations:int
    remaining_constraint_ids:tuple[str,...]
    collisions:tuple[tuple[str,str],...]
    fingerprint:str

def solve_layout(plan,*,constraints=(),safe_area=None,subtitle_zone=None,avoid_overlap=True):
    current=plan; iterations=0
    if safe_area is not None: current=enforce_safe_area(current,safe_area); iterations+=1
    if subtitle_zone is not None: current=enforce_subtitle_safe(current,subtitle_zone); iterations+=1
    if avoid_overlap: current=avoid_collisions(current); iterations+=1
    violations=evaluate_constraints(current,constraints)
    collisions=detect_collisions(current) if avoid_overlap else ()
    report=SolverReport(not violations and not collisions,iterations,tuple(v.constraint_id for v in violations),
                        tuple((c.a,c.b) for c in collisions),current.fingerprint)
    return current,report
