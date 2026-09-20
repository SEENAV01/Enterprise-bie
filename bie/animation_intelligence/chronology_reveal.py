from .temporal_contracts import *
def animate_chronology(ctx,chronology_id,events,dependency_edges=(),allow_simultaneous=True,exact_date_claims=False):
    events=tuple(events)
    if len(events)<2:raise TimeOrderError("need >=2 events")
    if len({e.event_id for e in events})!=len(events):raise TimeOrderError("duplicate events")
    for e in events:
        if e.source_ref not in ctx.evidence_refs:raise TimeGroundingError("ungrounded event")
    valid={e.event_id for e in events}; blockers=[];warnings=[]
    if exact_date_claims and any(e.uncertain for e in events):blockers.append("uncertain_event_not_exact")
    groups={}
    for e in events:
        if e.simultaneous_group:groups.setdefault(e.simultaneous_group,[]).append(e.event_id)
    if groups and not allow_simultaneous:blockers.append("simultaneous_events_not_allowed")
    edges=[]
    indeg={e.event_id:0 for e in events};adj={e.event_id:[] for e in events}
    for edge in dependency_edges:
        a=tok(edge["before"],"before");b=tok(edge["after"],"after")
        if a not in valid or b not in valid:raise TimeOrderError("unknown dependency event")
        if a==b:raise TimeOrderError("self dependency")
        edges.append((a,b));adj[a].append(b);indeg[b]+=1
    base=sorted(events,key=lambda e:(e.order_index if e.order_index is not None else 10**9,e.time_value if e.time_value is not None else 10**18,e.event_id))
    rank={e.event_id:i for i,e in enumerate(base)}
    ready=sorted([x for x,d in indeg.items() if d==0],key=lambda x:rank[x]);order=[]
    while ready:
        x=ready.pop(0);order.append(x)
        for y in adj[x]:
            indeg[y]-=1
            if indeg[y]==0:ready.append(y);ready.sort(key=lambda z:rank[z])
    if len(order)!=len(events):blockers.append("dependency_cycle")
    if any(e.uncertain for e in events):warnings.append("show_uncertainty")
    return plan(ctx,":chronology","chronology_reveal","BLOCKED" if blockers else ("REVIEW" if warnings or ctx.uncertainty>=.4 else "PASS"),
                ops=({"op":"chronology_reveal","chronology_id":chronology_id,"event_order":order,"simultaneous_groups":groups,"dependency_edges":edges,"exact_date_claims":exact_date_claims},),warnings=warnings,blockers=blockers)
