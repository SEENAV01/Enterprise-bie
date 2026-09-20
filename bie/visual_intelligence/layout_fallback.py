from __future__ import annotations
from dataclasses import dataclass
from .layout_contracts import Box, LayoutValidationError, make_layout_plan

class LayoutFallbackError(LayoutValidationError): pass

@dataclass(frozen=True)
class FallbackReport:
    mode:str
    preserved_required_ids:tuple[str,...]
    omitted_optional_ids:tuple[str,...]
    reason:str
    review_required:bool=True

def fallback_layout(plan,*,reason,allow_optional_omission=False):
    reason=str(reason).strip()
    if not reason: raise LayoutFallbackError("fallback reason is required")
    required=[n for n in plan.nodes if n.required]; optional=[n for n in plan.nodes if not n.required]
    chosen=required+([] if allow_optional_omission else optional)
    if not chosen: raise LayoutFallbackError("fallback cannot produce empty layout")
    chosen=sorted(chosen,key=lambda n:(-n.required,-n.priority,n.node_id))
    gap=.015; usable=.92-gap*(len(chosen)-1)
    if usable<=0: raise LayoutFallbackError("too many nodes for fallback")
    weights=[max(.05,n.box.height) for n in chosen]; total=sum(weights); y=.04; out=[]
    for node,w in zip(chosen,weights):
        h=usable*w/total
        if h<.025: raise LayoutFallbackError("fallback would make content unreadably small")
        out.append(node.with_box(Box(.06,y,.88,h))); y+=h+gap
    result=make_layout_plan(evidence_refs=plan.evidence_refs,reasoning_refs=plan.reasoning_refs,nodes=out,
                            constraints=plan.constraints,warnings=tuple(plan.warnings)+(f"layout-fallback:{reason}",))
    report=FallbackReport("single-column-preserve-required",tuple(sorted(n.node_id for n in required)),
                          tuple(sorted(n.node_id for n in optional)) if allow_optional_omission else (),reason,True)
    return result,report
