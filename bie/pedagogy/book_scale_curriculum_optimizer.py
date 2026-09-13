from dataclasses import dataclass
import heapq
import math

@dataclass(frozen=True)
class CurriculumUnit:
    unit_id:str; source_order:int; objective_priority:float; cognitive_load:float; review_weight:float; misconception_risk:float; estimated_minutes:float
@dataclass(frozen=True)
class CurriculumDependency:
    before:str; after:str; kind:str; hard:bool=True; strength:float=1.0
@dataclass(frozen=True)
class CurriculumPlan:
    order:tuple[str,...]; lesson_groups:tuple[tuple[str,...],...]; review_after_unit:tuple[tuple[str,int],...]; violated_soft_constraints:tuple[tuple[str,str,str],...]; total_minutes:float

def optimize_book_curriculum(units,dependencies,*,max_lesson_minutes=45.0,max_lesson_load=2.2):
    units=tuple(units); deps=tuple(dependencies)
    if any(type(x) not in (int,float) or not math.isfinite(x) or x<=0 for x in (max_lesson_minutes,max_lesson_load)):
        raise ValueError("finite positive lesson budgets required")
    if not units: raise ValueError("units")
    ids=[u.unit_id for u in units]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate")
    known=set(ids); by={u.unit_id:u for u in units}
    for u in units:
        if not u.unit_id.strip() or type(u.source_order) is not int or not math.isfinite(u.estimated_minutes): raise ValueError("unit identifier/order/duration")
        if u.source_order<0 or u.estimated_minutes<=0 or any(not 0<=x<=1 for x in (u.objective_priority,u.cognitive_load,u.review_weight,u.misconception_risk)): raise ValueError("unit")
        if u.estimated_minutes>max_lesson_minutes or u.cognitive_load>max_lesson_load:
            raise ValueError("unit exceeds lesson budget; split upstream before optimization")
    indeg={i:0 for i in ids}; adj={i:[] for i in ids}; soft=[]
    for d in deps:
        if type(d.hard) is not bool: raise ValueError("hard constraint flag must be boolean")
        if d.before not in known or d.after not in known or not 0<=d.strength<=1: raise ValueError("dep")
        if d.hard: adj[d.before].append(d.after); indeg[d.after]+=1
        else: soft.append(d)
    heap=[]
    for i in ids:
        if indeg[i]==0:
            u=by[i]; score=.45*u.objective_priority+.25*u.misconception_risk+.15*u.review_weight-.15*u.cognitive_load
            heapq.heappush(heap,(-round(score,8),u.source_order,u.unit_id))
    order=[]
    while heap:
        _,_,cur=heapq.heappop(heap); order.append(cur)
        for nxt in sorted(adj[cur]):
            indeg[nxt]-=1
            if indeg[nxt]==0:
                u=by[nxt]; score=.45*u.objective_priority+.25*u.misconception_risk+.15*u.review_weight-.15*u.cognitive_load
                heapq.heappush(heap,(-round(score,8),u.source_order,u.unit_id))
    if len(order)!=len(ids): raise ValueError("cycle")
    pos={x:i for i,x in enumerate(order)}
    violated=tuple(sorted((d.before,d.after,d.kind) for d in soft if pos[d.before]>=pos[d.after]))
    groups=[]; cur=[]; mins=load=0.0
    for uid in order:
        u=by[uid]
        if cur and (mins+u.estimated_minutes>max_lesson_minutes or load+u.cognitive_load>max_lesson_load):
            groups.append(tuple(cur)); cur=[]; mins=load=0.0
        cur.append(uid); mins+=u.estimated_minutes; load+=u.cognitive_load
    if cur: groups.append(tuple(cur))
    reviews=[]
    for idx,uid in enumerate(order):
        u=by[uid]; need=max(u.review_weight,u.misconception_risk)
        interval=1 if need>=.75 else 2 if need>=.45 else 4
        reviews.append((uid,idx+interval))
    return CurriculumPlan(tuple(order),tuple(groups),tuple(reviews),violated,math.fsum(u.estimated_minutes for u in units))
