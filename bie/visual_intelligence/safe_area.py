from __future__ import annotations
from dataclasses import dataclass
from .layout_contracts import Box, LayoutPlan, LayoutValidationError, plan_with_nodes, finite

class SafeAreaError(LayoutValidationError): pass

@dataclass(frozen=True)
class SafeArea:
    left:float=.04; top:float=.04; right:float=.04; bottom:float=.04
    def __post_init__(self):
        vals=[finite(v,field_name="safe_area") for v in (self.left,self.top,self.right,self.bottom)]
        if any(v<0 or v>=.45 for v in vals): raise SafeAreaError("safe-area margins must be in [0,0.45)")
        if self.left+self.right>=1 or self.top+self.bottom>=1: raise SafeAreaError("safe area has no usable canvas")
    @property
    def box(self): return Box(self.left,self.top,1-self.left-self.right,1-self.top-self.bottom)

def outside_safe_area(plan,area): return tuple(sorted(n.node_id for n in plan.nodes if not area.box.contains(n.box)))

def enforce_safe_area(plan,area,*,shrink=True):
    safe=area.box; out=[]; moved=[]
    for n in plan.nodes:
        b=n.box
        if safe.contains(b): out.append(n); continue
        if not shrink and n.required: raise SafeAreaError(f"required node {n.node_id} is outside safe area")
        w=min(b.width,safe.width); h=min(b.height,safe.height)
        x=min(max(b.x,safe.x),safe.right-w); y=min(max(b.y,safe.y),safe.bottom-h)
        out.append(n.with_box(Box(x,y,w,h))); moved.append(n.node_id)
    warnings=list(plan.warnings)
    if moved: warnings.append("safe-area-adjusted:"+",".join(sorted(moved)))
    return plan_with_nodes(plan,out,warnings=warnings)
