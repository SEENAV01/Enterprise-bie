from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from .layout_contracts import Box, LayoutNode, LayoutPlan, LayoutValidationError, finite

class GroupingError(LayoutValidationError): pass

@dataclass(frozen=True)
class SpatialGroup:
    group_id: str
    node_ids: tuple[str, ...]
    bounds: Box
    explicit: bool

def _bounds(nodes: Iterable[LayoutNode]) -> Box:
    ns=list(nodes)
    x=min(n.box.x for n in ns); y=min(n.box.y for n in ns)
    r=max(n.box.right for n in ns); b=max(n.box.bottom for n in ns)
    return Box(x,y,r-x,b-y)

def group_nodes(plan: LayoutPlan, *, proximity: float=.04) -> tuple[SpatialGroup,...]:
    p=finite(proximity,field_name="proximity")
    if p<0 or p>.5: raise GroupingError("proximity must be in [0,0.5]")
    explicit={}; ungrouped=[]
    for n in plan.nodes:
        (explicit.setdefault(n.group_id,[]).append(n) if n.group_id else ungrouped.append(n))
    groups=[]
    for gid in sorted(explicit):
        ns=explicit[gid]; groups.append(SpatialGroup(gid,tuple(sorted(n.node_id for n in ns)),_bounds(ns),True))
    remaining={n.node_id:n for n in ungrouped}; idx=1
    while remaining:
        seed=sorted(remaining)[0]; comp=[remaining.pop(seed)]; changed=True
        while changed:
            changed=False
            for nid in sorted(list(remaining)):
                n=remaining[nid]
                for c in comp:
                    cx,cy=c.box.center; nx,ny=n.box.center
                    dist=((cx-nx)**2+(cy-ny)**2)**.5
                    if dist<=p or (set(c.tags)&set(n.tags) and dist<=p*3):
                        comp.append(remaining.pop(nid)); changed=True; break
        groups.append(SpatialGroup(f"auto-{idx:03d}",tuple(sorted(n.node_id for n in comp)),_bounds(comp),False)); idx+=1
    return tuple(sorted(groups,key=lambda g:g.group_id))
