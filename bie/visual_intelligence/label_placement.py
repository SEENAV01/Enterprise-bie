from .text_contracts import *
from dataclasses import dataclass
@dataclass(frozen=True)
class LabelAnchor:
    anchor_id:str
    target_box:Box
    preferred_side:str="right"
SIDES=("right","left","top","bottom")
def place_label(intent, anchor, *, label_width=.18, label_height=.08, gap=.015, occupied=()):
    if intent.role!="label": raise TextVisualValidationError("label placement requires role=label")
    if anchor.preferred_side not in SIDES: raise PlacementError("unsupported preferred side")
    w=finite(label_width,field_name="label_width"); h=finite(label_height,field_name="label_height"); g=finite(gap,field_name="gap")
    if w<=0 or h<=0 or g<0: raise PlacementError("invalid label geometry")
    t=anchor.target_box
    sides=(anchor.preferred_side,)+tuple(s for s in SIDES if s!=anchor.preferred_side)
    candidates=[]
    for s in sides:
        if s=="right": x,y=t.right+g,t.y+t.height/2-h/2
        elif s=="left": x,y=t.x-w-g,t.y+t.height/2-h/2
        elif s=="top": x,y=t.x+t.width/2-w/2,t.y-h-g
        else: x,y=t.x+t.width/2-w/2,t.bottom+g
        if x<0 or y<0 or x+w>1 or y+h>1: continue
        b=Box(x,y,w,h)
        collisions=sum(1 for ob in occupied if b.intersects(ob))
        candidates.append((collisions,0 if s==anchor.preferred_side else 1,s,b))
    if not candidates:
        return decision(intent,action="escalate_label_placement",rationale=("no_in_canvas_candidate",))
    candidates.sort(key=lambda z:(z[0],z[1],z[2]))
    col,_,side,b=candidates[0]
    warnings=("label_collision_unresolved",) if col else ()
    return decision(intent,action="place_label",box=b,style={"anchor_id":anchor.anchor_id,"side":side},
                    rationale=(f"side={side}",f"collisions={col}"),warnings=warnings)
