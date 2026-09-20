from __future__ import annotations
from dataclasses import dataclass
from .layout_contracts import Box, LayoutPlan, LayoutValidationError, plan_with_nodes, finite

class ResponsiveCompositionError(LayoutValidationError): pass

@dataclass(frozen=True)
class Viewport:
    width:int
    height:int
    def __post_init__(self):
        if isinstance(self.width,bool) or isinstance(self.height,bool) or not isinstance(self.width,int) or not isinstance(self.height,int):
            raise ResponsiveCompositionError("viewport dimensions must be integers")
        if self.width<240 or self.height<240: raise ResponsiveCompositionError("viewport dimensions must be >=240")

def compose_responsive(plan:LayoutPlan, viewport:Viewport, *, gutter:float=.02)->LayoutPlan:
    g=finite(gutter,field_name="gutter")
    if g<0 or g>.1: raise ResponsiveCompositionError("gutter must be in [0,0.1]")
    aspect=viewport.width/viewport.height; nodes=list(plan.nodes); warnings=list(plan.warnings)
    if aspect<.85 and len(nodes)>1:
        ordered=sorted(nodes,key=lambda n:(-n.priority,n.box.y,n.box.x,n.node_id))
        available=.92-g*(len(ordered)-1)
        if available<=0: raise ResponsiveCompositionError("too many nodes for requested gutter")
        weights=[max(.08,n.box.height) for n in ordered]; total=sum(weights); y=.04; out=[]
        for n,w in zip(ordered,weights):
            h=available*w/total
            if h<.04: raise ResponsiveCompositionError("responsive stack would create unreadable node height")
            out.append(n.with_box(Box(.06,y,.88,h))); y+=h+g
        warnings.append("responsive:portrait_stack")
        return plan_with_nodes(plan,out,warnings=warnings)
    if aspect>2:
        out=[n.with_box(Box(.10+n.box.x*.80,n.box.y,n.box.width*.80,n.box.height)) for n in nodes]
        warnings.append("responsive:ultrawide_readable_band")
        return plan_with_nodes(plan,out,warnings=warnings)
    return plan_with_nodes(plan,nodes,warnings=warnings)
