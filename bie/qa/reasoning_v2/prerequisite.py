"""Prerequisite graph/readiness checks over a reviewed declared lesson schedule."""
from dataclasses import dataclass
import heapq
from ...prerequisite_intelligence.graph import Edge,build_graph
from ..source_v2.codec import loads
from ..release_v2.contracts import ContractError
from .context import Budget

@dataclass(frozen=True, slots=True)
class ReadinessWitness:
    event_id: str
    rule_id: str
    prerequisite: str
    status: str
    evidence_id: str


def check_prerequisites(c):
    r,p=c.request,c.policy; witnesses=[];budget=Budget(p.max_graph_checks)
    g=build_graph(p.concepts,tuple(Edge(x.prerequisite,x.dependent) for x in p.prerequisites))
    indegree={n:len(g.incoming[n]) for n in g.nodes};queue=[n for n in indegree if not indegree[n]];heapq.heapify(queue);order=[]
    while queue:
        n=heapq.heappop(queue);order.append(n)
        for child in sorted(g.outgoing[n]):
            indegree[child]-=1
            if indegree[child]==0:heapq.heappush(queue,child)
    if len(order)!=len(g.nodes):
        c.add('pr','PREREQUISITE_GRAPH_CYCLE','reasoning-scope','The operator prerequisite graph is cyclic; no cycle is silently removed.')
        return ()
    events=tuple(sorted(r.events,key=lambda e:e.position))
    for target in p.target_concepts:
        if not any(e.concept_id==target for e in events):
            c.add('pr','TARGET_CONCEPT_NOT_SCHEDULED',target,'An independently required target concept has no declared learning event.')
    usable_events=set()
    for e in events:
        if e.concept_id not in g.nodes:c.add('pr','UNKNOWN_EVENT_CONCEPT',e.event_id,'Event references a concept outside the policy graph.');continue
        if not c.actual_claims(e.claim_ids):c.add('pr','EVENT_CLAIM_MISSING',e.event_id,'Event credit must refer to real verified output claims.');continue
        if e.kind in ('teach','bridge') and ('teaching',e.event_id) in c.ready:
            # Question/instruction labels are not evidence that the concept was taught.
            if not any(c.claims[x].kind=='FACT' for x in e.claim_ids):
                c.add('pr','TEACHING_WITHOUT_EXPLANATORY_CONTENT',e.event_id,'A label, prompt or question alone does not teach the prerequisite.','REVIEW')
            else:usable_events.add(e.event_id)
    valid_masteries=[]
    for m in r.masteries:
        if m.concept_id not in g.nodes or m.learner_id!=p.learner_id:
            c.add('pr','MASTERY_SUBJECT_MISMATCH',m.observation_id,'Diagnostic belongs to another learner or unknown concept.');continue
        if m.observed_at>c.as_of or m.expires_at<=c.as_of or c.as_of-m.observed_at>p.max_mastery_age_seconds or m.expires_at-m.observed_at>p.max_mastery_age_seconds:
            c.add('pr','MASTERY_EVIDENCE_STALE',m.observation_id,'Diagnostic evidence is future-dated, expired or exceeds the policy lifetime.');continue
        payload=c.payloads.get(m.artifact.artifact_id)
        if payload is None:continue
        try:
            data=loads(payload)
            # Strict type-sensitive equality: True must not equal an integer score.
            from ..release_v2.contracts import canonical_bytes
            if canonical_bytes(data)!=canonical_bytes(m.payload()):raise ContractError('MASTERY_ARTIFACT_CONTENT_MISMATCH')
        except ContractError as exc:
            c.add('pr',exc.code,m.observation_id,'Verified diagnostic bytes do not match the declared scored observation.');continue
        if ('mastery',m.observation_id) in c.ready:valid_masteries.append(m)
    # A newer low diagnostic invalidates an older pass. Selecting just the best
    # result would launder contradictory learner evidence.
    byconcept={}
    for m in valid_masteries:byconcept.setdefault(m.concept_id,[]).append(m)
    for vals in byconcept.values():vals.sort(key=lambda m:(m.observed_at,m.available_at_position,m.observation_id))
    incoming={n:[] for n in g.nodes}
    for edge in p.prerequisites:incoming[edge.dependent].append(edge)
    ready_events=set()
    try:
        for e in events:
            if e.concept_id not in g.nodes:continue
            stack=[e.concept_id];seen=set();required={}
            while stack:
                n=stack.pop()
                if n in seen:continue
                seen.add(n)
                for edge in sorted(incoming[n],key=lambda x:x.rule_id):
                    budget.spend();required[edge.rule_id]=edge;stack.append(edge.prerequisite)
            all_ready=True
            for edge in sorted(required.values(),key=lambda x:x.rule_id):
                budget.spend();candidate=None;mode='MISSING'
                available=[m for m in byconcept.get(edge.prerequisite,()) if m.available_at_position<e.position]
                latest=max((m.observed_at for m in available),default=-1)
                latest_rows=[m for m in available if m.observed_at==latest]
                if latest_rows and min(m.score_ppm for m in latest_rows)>=edge.minimum_mastery_ppm:
                    candidate=min(latest_rows,key=lambda m:m.observation_id).observation_id;mode='DIAGNOSTIC_MASTERY'
                if candidate is None and edge.mode=='instruction_or_mastery':
                    for prior in events:
                        budget.spend()
                        if prior.position>=e.position:break
                        if (prior.concept_id==edge.prerequisite and prior.depth>=edge.minimum_depth and
                            prior.event_id in usable_events and prior.event_id in ready_events):
                            candidate=prior.event_id;mode='PRIOR_INSTRUCTION'
                if candidate is None:
                    all_ready=False
                    c.add('pr','PREREQUISITE_NOT_READY',e.event_id,
                          f'{edge.rule_id}: {edge.prerequisite} must be ready before this event; later instruction, self-reference and unverified scores earn no credit.')
                witnesses.append(ReadinessWitness(e.event_id,edge.rule_id,edge.prerequisite,mode,candidate or ''))
            if all_ready:ready_events.add(e.event_id)
    except ContractError as exc:
        c.add('pr',exc.code,'reasoning-scope','Readiness scope exceeds the configured budget; partial traversal is not a pass.')
    c.metrics['pr'].update(graph_nodes=len(g.nodes),graph_edges=len(p.prerequisites),events=len(events),
                          readiness_obligations_checked=len(witnesses),readiness_obligations_met=sum(w.status!='MISSING' for w in witnesses),graph_checks=budget.used)
    return tuple(witnesses)
