from __future__ import annotations
from dataclasses import dataclass,replace
from math import isfinite

class SolverError(ValueError): pass
@dataclass(frozen=True)
class Box:
    x:float;y:float;width:float;height:float
    def __post_init__(self):
        vals=[float(self.x),float(self.y),float(self.width),float(self.height)]
        if not all(isfinite(v) for v in vals) or self.width<=0 or self.height<=0: raise SolverError("bad box")
    @property
    def right(self):return self.x+self.width
    @property
    def bottom(self):return self.y+self.height
@dataclass(frozen=True)
class Node:
    node_id:str; box:Box; required:bool=True
@dataclass(frozen=True)
class Constraint:
    constraint_id:str;kind:str;node_ids:tuple[str,...];value:float|None=None;hard:bool=True
@dataclass(frozen=True)
class SolveReport:
    solved:bool;iterations:int;unsat_core:tuple[str,...];repairs:tuple[str,...];nodes:tuple[Node,...];review_required:bool=True;accepted:bool=False

def _clamp(b):
    w=min(b.width,1);h=min(b.height,1);x=min(max(b.x,0),1-w);y=min(max(b.y,0),1-h);return Box(x,y,w,h)
def _violation(c,n):
    a=n[c.node_ids[0]].box; b=n[c.node_ids[1]].box if len(c.node_ids)>1 else None;v=c.value or 0
    if c.kind=="contains":return max(a.x-b.x,a.y-b.y,b.right-a.right,b.bottom-a.bottom,0)
    if c.kind=="left_of":return max(0,a.right+v-b.x)
    if c.kind=="above":return max(0,a.bottom+v-b.y)
    if c.kind=="align_left":return abs(a.x-b.x)
    if c.kind=="align_top":return abs(a.y-b.y)
    if c.kind=="min_gap_x":
        l,r=(a,b) if a.x<=b.x else (b,a);return max(0,v-(r.x-l.right))
    if c.kind=="min_gap_y":
        t,bt=(a,b) if a.y<=b.y else (b,a);return max(0,v-(bt.y-t.bottom))
    if c.kind=="non_overlap":return max(0,min(a.right,b.right)-max(a.x,b.x))*max(0,min(a.bottom,b.bottom)-max(a.y,b.y))
    if c.kind=="min_width":return max(0,v-a.width)
    if c.kind=="min_height":return max(0,v-a.height)
    raise SolverError("unsupported constraint "+c.kind)

def _repair(c,n):
    ids=c.node_ids;a=n[ids[0]];b=n[ids[1]] if len(ids)>1 else None;v=c.value or 0
    A=a.box;B=b.box if b else None
    if c.kind=="contains":
        child=b; x=min(max(B.x,A.x),A.right-B.width);y=min(max(B.y,A.y),A.bottom-B.height)
        if B.width>A.width or B.height>A.height:return False
        n[child.node_id]=replace(child,box=Box(x,y,B.width,B.height));return True
    if c.kind=="align_left": n[b.node_id]=replace(b,box=_clamp(Box(A.x,B.y,B.width,B.height)));return True
    if c.kind=="align_top": n[b.node_id]=replace(b,box=_clamp(Box(B.x,A.y,B.width,B.height)));return True
    if c.kind=="left_of":
        x=A.right+v
        if x+B.width>1:return False
        n[b.node_id]=replace(b,box=Box(x,B.y,B.width,B.height));return True
    if c.kind=="above":
        y=A.bottom+v
        if y+B.height>1:return False
        n[b.node_id]=replace(b,box=Box(B.x,y,B.width,B.height));return True
    if c.kind=="min_gap_x":
        l,r=(a,b) if A.x<=B.x else (b,a);L=l.box;R=r.box;x=L.right+v
        if x+R.width>1:return False
        n[r.node_id]=replace(r,box=Box(x,R.y,R.width,R.height));return True
    if c.kind=="min_gap_y":
        t,bt=(a,b) if A.y<=B.y else (b,a);T=t.box;D=bt.box;y=T.bottom+v
        if y+D.height>1:return False
        n[bt.node_id]=replace(bt,box=Box(D.x,y,D.width,D.height));return True
    if c.kind=="non_overlap":
        options=[(A.right+v,B.y),(A.x-B.width-v,B.y),(B.x,A.bottom+v),(B.x,A.y-B.height-v)]
        for x,y in options:
            if x>=0 and y>=0 and x+B.width<=1 and y+B.height<=1:
                n[b.node_id]=replace(b,box=Box(x,y,B.width,B.height));return True
        return False
    if c.kind=="min_width":
        if v<=0 or v>1:return False
        n[a.node_id]=replace(a,box=_clamp(Box(A.x,A.y,v,A.height)));return True
    if c.kind=="min_height":
        if v<=0 or v>1:return False
        n[a.node_id]=replace(a,box=_clamp(Box(A.x,A.y,A.width,v)));return True
    return False

def solve(nodes,constraints,max_iterations=100,tolerance=1e-6):
    n={x.node_id:x for x in nodes}
    if len(n)!=len(tuple(nodes)):raise SolverError("duplicate node ids")
    cs=tuple(constraints);repairs=[]
    for iteration in range(1,max_iterations+1):
        violated=[c for c in cs if _violation(c,n)>tolerance]
        if not violated:return SolveReport(True,iteration-1,(),tuple(repairs),tuple(n[k] for k in sorted(n)))
        progress=False;failed=[]
        for c in violated:
            if _repair(c,n):repairs.append(c.constraint_id);progress=True
            elif c.hard:failed.append(c.constraint_id)
        if failed:return SolveReport(False,iteration,tuple(sorted(set(failed))),tuple(repairs),tuple(n[k] for k in sorted(n)))
        if not progress:break
    unsat=tuple(sorted(c.constraint_id for c in cs if c.hard and _violation(c,n)>tolerance))
    return SolveReport(not unsat,max_iterations,unsat,tuple(repairs),tuple(n[k] for k in sorted(n)))
