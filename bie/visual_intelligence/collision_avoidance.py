from __future__ import annotations
from dataclasses import dataclass
from .layout_contracts import Box, LayoutValidationError, plan_with_nodes, finite

class CollisionError(LayoutValidationError): pass

@dataclass(frozen=True)
class Collision:
    a:str; b:str; area:float

def detect_collisions(plan,*,ignore_same_group=False):
    out=[]; ns=sorted(plan.nodes,key=lambda n:n.node_id)
    for i,a in enumerate(ns):
        for b in ns[i+1:]:
            if ignore_same_group and a.group_id and a.group_id==b.group_id: continue
            area=a.box.intersection_area(b.box)
            if area>1e-9: out.append(Collision(a.node_id,b.node_id,area))
    return tuple(out)

def avoid_collisions(plan,*,gap=.015,max_iterations=100):
    g=finite(gap,field_name="gap")
    if g<0 or g>.1: raise CollisionError("gap must be in [0,0.1]")
    if not isinstance(max_iterations,int) or max_iterations<=0: raise CollisionError("max_iterations must be positive integer")
    nodes={n.node_id:n for n in plan.nodes}
    for _ in range(max_iterations):
        current=plan_with_nodes(plan,[nodes[k] for k in sorted(nodes)])
        cs=detect_collisions(current)
        if not cs:
            warnings=list(plan.warnings)
            if any(nodes[n.node_id].box!=n.box for n in plan.nodes): warnings.append("collision-avoidance-applied")
            return plan_with_nodes(plan,[nodes[n.node_id] for n in plan.nodes],warnings=warnings)
        c=cs[0]; a,b=nodes[c.a],nodes[c.b]
        mover,fixed=(a,b) if (a.priority,a.node_id)<(b.priority,b.node_id) else (b,a)
        if a.required and b.required and a.priority==100 and b.priority==100:
            raise CollisionError("two pinned-critical nodes collide")
        positions=[(fixed.box.right+g,mover.box.y),(fixed.box.x-mover.box.width-g,mover.box.y),
                   (mover.box.x,fixed.box.bottom+g),(mover.box.x,fixed.box.y-mover.box.height-g)]
        candidates=[]
        for x,y in positions:
            if x>=0 and y>=0 and x+mover.box.width<=1 and y+mover.box.height<=1:
                box=Box(x,y,mover.box.width,mover.box.height)
                overlap=sum(box.intersection_area(n.box) for nid,n in nodes.items() if nid!=mover.node_id)
                move=abs(x-mover.box.x)+abs(y-mover.box.y)
                candidates.append((overlap,move,x,y,box))
        if not candidates: raise CollisionError(f"cannot relocate {mover.node_id} without leaving canvas")
        candidates.sort(key=lambda x:(round(x[0],12),round(x[1],12),x[2],x[3]))
        nodes[mover.node_id]=mover.with_box(candidates[0][-1])
    raise CollisionError("collision solver exceeded max_iterations")
