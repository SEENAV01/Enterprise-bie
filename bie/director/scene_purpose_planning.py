from .contract_validation import nonblank,items,ids,finite
from dataclasses import dataclass
@dataclass(frozen=True)
class ScenePurpose: scene_id:str; purpose:str; objective_ids:tuple[str,...]; evidence_ids:tuple[str,...]; rationale:str
def plan_scene_purposes(rows):
    raw=items(rows,"scene purpose rows"); normalized=[]
    supported={"EXPLANATION","INQUIRY","DERIVATION","SIMULATION"}
    for row in raw:
        row=items(row,"scene purpose row")
        if len(row)!=3: raise ValueError("objective, mode and evidence required")
        o,m,ev=row; nonblank(o,"objective"); nonblank(m,"mode")
        if m not in supported: raise ValueError("unresolved teaching mode")
        normalized.append((o,m,ids(ev,"scene purpose evidence",canonical=True)))
    rows=tuple(normalized)
    if not rows: raise ValueError("rows")
    all_o=tuple(sorted({o for o,_,_ in rows})); all_e=tuple(sorted({e for _,_,ev in rows for e in ev}))
    out=[ScenePurpose("scene-001","HOOK",all_o,all_e,"attention/relevance")]; i=2
    mp={"EXPLANATION":"EXPLAIN","INQUIRY":"DEMONSTRATE","DERIVATION":"DERIVE","SIMULATION":"SIMULATE"}
    for o,m,ev in rows:
        if not o.strip() or not ev: raise ValueError("grounding")
        out.append(ScenePurpose(f"scene-{i:03d}",mp.get(m,"EXPLAIN"),(o,),tuple(sorted(set(ev))),f"mode={m}")); i+=1
    out.append(ScenePurpose(f"scene-{i:03d}","RECAP",all_o,all_e,"consolidation"))
    return tuple(out)
