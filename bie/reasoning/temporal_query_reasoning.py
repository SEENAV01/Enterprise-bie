"""RE-TEMP-008: explainable temporal reachability queries over grounded strict-before constraints."""
from __future__ import annotations
from dataclasses import asdict
from collections import deque
from bie.reasoning.temporal_constraint_reasoning import TemporalConstraint
from bie.reasoning.grounded_result import evidence, identifier, inference, require_refs
TASK_ID="BIE-RE-TEMP-008"

def explain_before(event_ids,constraints,left,right,refs):
    refs=evidence(refs); ids=tuple(sorted(event_ids)); known=set(ids)
    if len(ids)!=len(known) or not ids: raise ValueError("Unique event ids required")
    for x in ids: identifier(x,"event id")
    identifier(left,"left event id"); identifier(right,"right event id")
    if left not in known or right not in known or left==right: raise ValueError("Query endpoints must be known distinct events")
    adj={x:[] for x in ids}; constraints=tuple(sorted(constraints,key=lambda c:(c.before,c.after,c.evidence_ids)))
    seen=set()
    for c in constraints:
        if not isinstance(c,TemporalConstraint): raise ValueError("Expected TemporalConstraint")
        if c.before not in known or c.after not in known or c.before==c.after: raise ValueError("Constraint endpoints must be known distinct events")
        require_refs(c.evidence_ids,refs); edge=(c.before,c.after)
        if edge in seen: raise ValueError("Duplicate temporal constraint")
        seen.add(edge); adj[c.before].append((c.after,tuple(sorted(c.evidence_ids))))
    def path(src,dst):
        q=deque([(src,[src],set())]); visited={src}
        while q:
            node,p,ev=q.popleft()
            for nxt,refs2 in sorted(adj[node]):
                nev=ev|set(refs2)
                if nxt==dst:return p+[nxt],sorted(nev)
                if nxt not in visited: visited.add(nxt);q.append((nxt,p+[nxt],nev))
        return None,[]
    forward,fe=path(left,right); reverse,re=path(right,left)
    if forward and reverse:
        status="CONFLICT"; relation="inconsistent"; chosen=[]; ev=sorted(set(fe+re)); unc=("Both directions are derivable, so the strict temporal graph is cyclic",)
    elif forward:
        status="RESOLVED"; relation="before"; chosen=forward; ev=fe; unc=()
    elif reverse:
        status="RESOLVED"; relation="after"; chosen=reverse; ev=re; unc=()
    else:
        status="AMBIGUOUS"; relation="indeterminate"; chosen=[]; ev=[]; unc=("No strict-before path establishes either direction",)
    value={"left":left,"right":right,"relation":relation,"witness_path":chosen,"witness_evidence_ids":ev}
    return inference(TASK_ID,"temporal.explain_query",{"event_ids":ids,"constraints":[asdict(c) for c in constraints],"left":left,"right":right},value,refs,status=status,assumptions=("Reachability proves only the supplied/transitive strict-before relation, not causation",),uncertainty=unc)
