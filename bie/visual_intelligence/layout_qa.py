from __future__ import annotations
from dataclasses import dataclass
from .visual_qa_contracts import Box, LayoutQAError, token, make_result

@dataclass(frozen=True)
class LayoutElement:
    element_id: str
    role: str
    box: Box
    required: bool = True
    def __post_init__(self):
        object.__setattr__(self,"element_id",token(self.element_id,"element_id"))
        object.__setattr__(self,"role",token(self.role,"role"))

def evaluate_layout_qa(elements, evidence_refs, reasoning_refs, safe_margin=.03, min_area=.0025, subtitle_zone=None):
    elems=tuple(elements)
    if not elems: raise LayoutQAError("layout must contain elements")
    if len({e.element_id for e in elems}) != len(elems): raise LayoutQAError("duplicate element ids")
    outside=[]; too_small=[]; subtitle=[]; collisions=[]
    for e in elems:
        b=e.box
        if e.required and (b.x<safe_margin or b.y<safe_margin or b.right>1-safe_margin or b.bottom>1-safe_margin): outside.append(e.element_id)
        if e.required and b.area<min_area: too_small.append(e.element_id)
        if subtitle_zone and e.required and e.role!="subtitle" and b.intersection_area(subtitle_zone)>1e-9: subtitle.append(e.element_id)
    ordered=sorted(elems,key=lambda x:x.element_id)
    for i,a in enumerate(ordered):
        for b in ordered[i+1:]:
            area=a.box.intersection_area(b.box)
            if area>1e-9 and (a.required or b.required): collisions.append((a.element_id,b.element_id,round(area,6)))
    blockers=[]
    if outside: blockers.append("outside_safe_area")
    if too_small: blockers.append("below_min_area")
    if collisions: blockers.append("required_collisions")
    if subtitle: blockers.append("subtitle_conflict")
    value=max(0.0,1-.15*len(outside)-.12*len(too_small)-.18*len(collisions)-.10*len(subtitle))
    return make_result("vis-layout","layout_qa",value,blockers,[],evidence_refs,reasoning_refs,{
        "outside":outside,"too_small":too_small,"collisions":collisions,"subtitle_conflicts":subtitle
    })
