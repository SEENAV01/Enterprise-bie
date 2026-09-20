from __future__ import annotations
from dataclasses import dataclass
from .layout_contracts import Box, LayoutValidationError, plan_with_nodes, finite

class SubtitleSafeError(LayoutValidationError): pass

@dataclass(frozen=True)
class SubtitleZone:
    height:float=.16
    bottom_margin:float=.03
    def __post_init__(self):
        h=finite(self.height,field_name="subtitle.height"); m=finite(self.bottom_margin,field_name="subtitle.bottom_margin")
        if h<=0 or h>=.5 or m<0 or h+m>=.5: raise SubtitleSafeError("invalid subtitle zone")
        object.__setattr__(self,"height",h); object.__setattr__(self,"bottom_margin",m)
    @property
    def box(self): return Box(0,1-self.bottom_margin-self.height,1,self.height)

def subtitle_conflicts(plan,zone):
    return tuple(sorted(n.node_id for n in plan.nodes if n.box.overlaps(zone.box) and "subtitle" not in n.tags))

def enforce_subtitle_safe(plan,zone,*,gap=.02):
    g=finite(gap,field_name="gap")
    if g<0 or g>.1: raise SubtitleSafeError("gap must be in [0,0.1]")
    ceiling=zone.box.y-g; out=[]; moved=[]
    for n in plan.nodes:
        if "subtitle" in n.tags or not n.box.overlaps(zone.box): out.append(n); continue
        h=min(n.box.height,max(.04,ceiling)); y=max(0,min(n.box.y,ceiling-h))
        if y+h>ceiling+1e-9: raise SubtitleSafeError(f"node {n.node_id} cannot be relocated")
        out.append(n.with_box(Box(n.box.x,y,n.box.width,h))); moved.append(n.node_id)
    warnings=list(plan.warnings)
    if moved: warnings.append("subtitle-safe-adjusted:"+",".join(sorted(moved)))
    return plan_with_nodes(plan,out,warnings=warnings)
