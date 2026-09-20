from .text_contracts import *
from dataclasses import dataclass
@dataclass(frozen=True)
class AnnotationTarget:
    target_id:str
    target_box:Box
def place_annotation(intent, target, *, width=.25, height=.12, margin=.02, occupied=()):
    if intent.role!="annotation": raise TextVisualValidationError("annotation placement requires role=annotation")
    w=finite(width,field_name="width"); h=finite(height,field_name="height"); m=finite(margin,field_name="margin")
    if w<=0 or h<=0 or m<0: raise PlacementError("invalid annotation geometry")
    t=target.target_box
    positions=[
        ("bottom_right",t.right+m,t.bottom+m),
        ("top_right",t.right+m,t.y-h-m),
        ("bottom_left",t.x-w-m,t.bottom+m),
        ("top_left",t.x-w-m,t.y-h-m),
    ]
    cand=[]
    for name,x,y in positions:
        if x<0 or y<0 or x+w>1 or y+h>1: continue
        b=Box(x,y,w,h)
        if b.intersects(t): continue
        collisions=sum(1 for ob in occupied if b.intersects(ob))
        distance=abs(b.x-t.x)+abs(b.y-t.y)
        cand.append((collisions,distance,name,b))
    if not cand:
        return decision(intent,action="escalate_annotation_placement",rationale=("no_safe_annotation_region",))
    cand.sort(key=lambda z:(z[0],round(z[1],6),z[2]))
    c,_,name,b=cand[0]
    warnings=("annotation_collision_unresolved",) if c else ()
    return decision(intent,action="place_annotation",box=b,
                    style={"target_id":target.target_id,"placement":name,"leader_line":True},
                    rationale=(f"placement={name}",f"collisions={c}"),warnings=warnings)
