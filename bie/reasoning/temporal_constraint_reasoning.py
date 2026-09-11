"""RE-TEMP-006: temporal constraint closure with provenance paths and contradiction witnesses."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from collections import deque
from bie.reasoning.grounded_result import evidence, identifier, inference, require_refs
TASK_ID="BIE-RE-TEMP-006"

@dataclass(frozen=True)
class TemporalConstraint:
    before:str
    after:str
    evidence_ids:tuple[str,...]


def constraint_closure(event_ids,constraints,refs):
    refs=evidence(refs); ids=tuple(sorted(event_ids))
    if not ids: raise ValueError("At least one event id required")
    if len(ids)!=len(set(ids)): raise ValueError("Duplicate event id")
    for x in ids: identifier(x,"event id")
    known=set(ids); constraints=tuple(sorted(constraints,key=lambda c:(c.before,c.after,c.evidence_ids)))
    adj={x:set() for x in ids}; edge_refs={}
    for c in constraints:
        if c.before not in known or c.after not in known or c.before==c.after: raise ValueError("Constraint endpoints must be known distinct events")
        require_refs(c.evidence_ids,refs); edge=(c.before,c.after)
        if edge in edge_refs: raise ValueError("Duplicate temporal constraint")
        adj[c.before].add(c.after); edge_refs[edge]=tuple(sorted(c.evidence_ids))
    closure=[]; contradiction=None
    for src in ids:
        q=deque([(src,[src],set())]); seen={src}
        while q:
            node,path,prov=q.popleft()
            for nxt in sorted(adj[node]):
                nprov=prov|set(edge_refs[(node,nxt)]); npath=path+[nxt]
                if nxt==src:
                    contradiction={"cycle":npath,"evidence_ids":sorted(nprov)}; break
                if nxt not in seen:
                    seen.add(nxt); q.append((nxt,npath,nprov))
                    closure.append({"before":src,"after":nxt,"path":npath,"evidence_ids":sorted(nprov),"derived":len(npath)>2})
            if contradiction: break
        if contradiction: break
    value={"closure":[] if contradiction else sorted(closure,key=lambda x:(x['before'],x['after'],x['path'])),"contradiction_witness":contradiction}
    return inference(TASK_ID,"temporal.constraint_closure",{"event_ids":ids,"constraints":[asdict(c) for c in constraints]},value,refs,status="CONFLICT" if contradiction else "RESOLVED",uncertainty=("A temporal cycle makes strict-before constraints inconsistent",) if contradiction else ())
