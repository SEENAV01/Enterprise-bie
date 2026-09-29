"""Reuse PR/RE trust management. No embedded operational keys or PASS override."""
from ..reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier

def review_targets(request):
    claims={c.claim_id:c for c in request.source.claims};events={e.event_id:e for e in request.events}
    out={('inventory','pedagogy-scope'):tuple(sorted(claims)),
         ('teaching','load-policy'):('load-policy',)}
    for o in request.objectives:
        out[('mapping',o.objective_id)]=tuple(sorted(set(o.statement_claim_ids+o.citation_ids)))
    for e in request.events:
        out[('mapping',e.event_id)]=tuple(sorted(set((e.event_id,)+e.claim_ids)))
    for t in request.teachings:
        out[('teaching',t.teaching_id)]=tuple(sorted(set(t.event_ids)|{c for eid in t.event_ids if eid in events for c in events[eid].claim_ids}))
    for item in request.items:
        out[('mapping',item.item_id)]=tuple(sorted(set((item.prompt_event_id,item.solution_event_id,item.feedback_event_id)+item.rubric_claim_ids)))
        out[('support',item.item_id)]=out[('mapping',item.item_id)]
    for r in request.routes:out[('inventory',r.route_id)]=tuple(sorted(r.segment_ids))
    return out
