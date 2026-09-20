from dataclasses import dataclass
from math import ceil,sqrt
from .unified_scene_ir_codec import decode_scene_ir

@dataclass(frozen=True)
class SpatialResolutionReceipt:
    scene_id:str;input_fingerprint:str;output_fingerprint:str;resolved_boxes:tuple;iterations:int
    blockers:tuple[str,...];warnings:tuple[str,...];passed:bool;accepted:bool=False

def _box(b):
    return {"x":float(b["x"]),"y":float(b["y"]),"width":float(b["width"]),"height":float(b["height"])}

def _default(ids):
    n=max(1,len(ids));cols=max(1,ceil(sqrt(n)));rows=ceil(n/cols);gap=.02
    bw=(1-gap*(cols+1))/cols;bh=(1-gap*(rows+1))/rows
    return {eid:{"x":gap+(i%cols)*(bw+gap),"y":gap+(i//cols)*(bh+gap),"width":bw,"height":bh} for i,eid in enumerate(ids)}

def _ok(b):
    return b["x"]>=-1e-9 and b["y"]>=-1e-9 and b["width"]>0 and b["height"]>0 and b["x"]+b["width"]<=1+1e-9 and b["y"]+b["height"]<=1+1e-9

def _satisfies(c,boxes,tol=1e-6):
    s=boxes[c["subject_id"]];r=boxes[c["reference_id"]];g=float(c.get("gap",0));rel=c["relation"]
    if rel=="left_of":return s["x"]+s["width"]+g<=r["x"]+tol
    if rel=="right_of":return s["x"]>=r["x"]+r["width"]+g-tol
    if rel=="above":return s["y"]+s["height"]+g<=r["y"]+tol
    if rel=="below":return s["y"]>=r["y"]+r["height"]+g-tol
    if rel=="inside":return s["x"]>=r["x"]-tol and s["y"]>=r["y"]-tol and s["x"]+s["width"]<=r["x"]+r["width"]+tol and s["y"]+s["height"]<=r["y"]+r["height"]+tol
    if rel=="near":
        sc=(s["x"]+s["width"]/2,s["y"]+s["height"]/2);rc=(r["x"]+r["width"]/2,r["y"]+r["height"]/2)
        return abs(sc[0]-rc[0])+abs(sc[1]-rc[1])<=max(.25,g)+tol
    return False

def _apply(c,boxes):
    s=boxes[c["subject_id"]];r=boxes[c["reference_id"]];g=float(c.get("gap",0));rel=c["relation"]
    if rel=="left_of" and not _satisfies(c,boxes):
        if s["width"]+g+r["width"]>1:return
        s["x"]=max(0,min(s["x"],1-s["width"]-g-r["width"]))
        r["x"]=max(r["x"],s["x"]+s["width"]+g)
        if r["x"]+r["width"]>1:
            r["x"]=1-r["width"];s["x"]=r["x"]-g-s["width"]
    elif rel=="right_of" and not _satisfies(c,boxes):
        if s["width"]+g+r["width"]>1:return
        r["x"]=max(0,min(r["x"],1-r["width"]-g-s["width"]))
        s["x"]=max(s["x"],r["x"]+r["width"]+g)
        if s["x"]+s["width"]>1:
            s["x"]=1-s["width"];r["x"]=s["x"]-g-r["width"]
    elif rel=="above" and not _satisfies(c,boxes):
        if s["height"]+g+r["height"]>1:return
        s["y"]=max(0,min(s["y"],1-s["height"]-g-r["height"]))
        r["y"]=max(r["y"],s["y"]+s["height"]+g)
        if r["y"]+r["height"]>1:
            r["y"]=1-r["height"];s["y"]=r["y"]-g-s["height"]
    elif rel=="below" and not _satisfies(c,boxes):
        if s["height"]+g+r["height"]>1:return
        r["y"]=max(0,min(r["y"],1-r["height"]-g-s["height"]))
        s["y"]=max(s["y"],r["y"]+r["height"]+g)
        if s["y"]+s["height"]>1:
            s["y"]=1-s["height"];r["y"]=s["y"]-g-r["height"]
    elif rel=="inside":
        if s["width"]>r["width"] or s["height"]>r["height"]:return
        s["x"]=min(max(s["x"],r["x"]),r["x"]+r["width"]-s["width"])
        s["y"]=min(max(s["y"],r["y"]),r["y"]+r["height"]-s["height"])
    elif rel=="near":
        s["x"]=min(1-s["width"],max(0,r["x"]+(r["width"]-s["width"])/2))
        s["y"]=min(1-s["height"],max(0,r["y"]+(r["height"]-s["height"])/2))

def _align(a,boxes):
    ids=tuple(a.get("element_ids",()))
    if len(ids)<2:return
    axis=a.get("axis");mode=a.get("mode")
    if mode=="distribute":
        ordered=sorted(ids,key=lambda eid:boxes[eid]["x" if axis=="x" else "y"])
        if axis=="x":
            first,last=boxes[ordered[0]],boxes[ordered[-1]]
            span=(last["x"]-first["x"])/(len(ordered)-1)
            for i,eid in enumerate(ordered):boxes[eid]["x"]=min(1-boxes[eid]["width"],max(0,first["x"]+i*span))
        else:
            first,last=boxes[ordered[0]],boxes[ordered[-1]]
            span=(last["y"]-first["y"])/(len(ordered)-1)
            for i,eid in enumerate(ordered):boxes[eid]["y"]=min(1-boxes[eid]["height"],max(0,first["y"]+i*span))
        return
    ref=boxes[ids[0]]
    for eid in ids[1:]:
        b=boxes[eid]
        if axis=="x":
            target=ref["x"] if mode=="start" else ref["x"]+ref["width"]/2 if mode=="center" else ref["x"]+ref["width"]
            b["x"]=target if mode=="start" else target-b["width"]/2 if mode=="center" else target-b["width"]
            b["x"]=min(1-b["width"],max(0,b["x"]))
        elif axis=="y":
            target=ref["y"] if mode=="start" else ref["y"]+ref["height"]/2 if mode=="center" else ref["y"]+ref["height"]
            b["y"]=target if mode=="start" else target-b["height"]/2 if mode=="center" else target-b["height"]
            b["y"]=min(1-b["height"],max(0,b["y"]))

def resolve_spatial_constraints(document,max_iterations=16):
    ids=[e.element_id for e in document.elements];boxes=_default(ids)
    for e in document.elements:
        if e.normalized_box is not None:boxes[e.element_id]=_box(dict(e.normalized_box))
    for raw in document.layout.get("boxes",()):
        if raw.get("element_id") in boxes:boxes[raw["element_id"]]=_box(raw)
    rels=sorted((dict(x) for x in document.layout.get("relative_constraints",())),key=lambda x:(int(x.get("priority",100)),str(x.get("constraint_id",""))))
    aligns=sorted((dict(x) for x in document.layout.get("alignment_constraints",())),key=lambda x:str(x.get("constraint_id","")))
    blockers=[];warnings=[]
    for c in rels:
        if c.get("subject_id") not in boxes or c.get("reference_id") not in boxes:blockers.append("unknown_relative_constraint_element:"+str(c.get("constraint_id","?")))
        if c.get("relation") not in {"left_of","right_of","above","below","inside","near"}:blockers.append("unsupported_relative_relation:"+str(c.get("constraint_id","?")))
    for a in aligns:
        if any(e not in boxes for e in a.get("element_ids",())):blockers.append("unknown_alignment_element:"+str(a.get("constraint_id","?")))
        if a.get("axis") not in {"x","y"} or a.get("mode") not in {"start","center","end","distribute"}:blockers.append("unsupported_alignment:"+str(a.get("constraint_id","?")))
    if blockers:
        return document,SpatialResolutionReceipt(document.scene_id,document.fingerprint,document.fingerprint,(),0,tuple(sorted(set(blockers))),(),False,False)
    iterations=0
    for iterations in range(1,max_iterations+1):
        before=tuple((eid,tuple(round(boxes[eid][k],9) for k in ("x","y","width","height"))) for eid in sorted(boxes))
        for c in rels:_apply(c,boxes)
        for a in aligns:_align(a,boxes)
        after=tuple((eid,tuple(round(boxes[eid][k],9) for k in ("x","y","width","height"))) for eid in sorted(boxes))
        if before==after:break
    for eid,b in boxes.items():
        if not _ok(b):blockers.append("resolved_box_out_of_bounds:"+eid)
    for c in rels:
        if not _satisfies(c,boxes):blockers.append("unsatisfied_relative_constraint:"+str(c.get("constraint_id","?")))
    payload=document.to_dict()
    for e in payload["elements"]:e["normalized_box"]=boxes[e["element_id"]]
    layout=dict(payload.get("layout",{}));layout["boxes"]=[{"element_id":eid,**boxes[eid]} for eid in sorted(boxes)];layout["resolved"]=not blockers
    payload["layout"]=layout;payload.pop("fingerprint",None)
    resolved=decode_scene_ir(payload)
    receipt=SpatialResolutionReceipt(document.scene_id,document.fingerprint,resolved.fingerprint,tuple((eid,tuple((k,boxes[eid][k]) for k in ("x","y","width","height"))) for eid in sorted(boxes)),iterations,tuple(sorted(set(blockers))),tuple(sorted(set(warnings))),not blockers,False)
    return resolved,receipt
