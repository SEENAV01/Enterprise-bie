"""Reuse purpose-scoped PR/RE review trust. No operational signing keys."""
from ..reasoning_v2.attestation import Review, ReviewKey, ReviewVerifier


def review_targets(request, policy):
    targets={('inventory','visual-scope'):tuple(sorted(e.object_id for e in request.elements))}
    for s in request.scenes: targets[('teaching',s.scene_id)]=tuple(sorted(s.objective_ids))
    for e in request.elements:
        targets[('mapping',e.object_id)]=tuple(sorted(set((e.object_id,)+e.claim_ids)))
    for s in request.states:
        targets[('inventory',s.state_id)]=tuple(sorted(m.object_id for m in s.measurements)) or (s.state_id,)
    for r in request.relations:
        targets[('mapping',r.relation_id)]=tuple(sorted(set((r.from_id,r.to_id)+r.claim_ids)))
    for a in policy.overlaps:
        targets[('support',a.allowance_id)]=tuple(sorted((a.first_id,a.second_id)))
    for c in request.captures:
        targets[('mapping',c.capture_id)]=tuple(sorted((c.html.artifact_id,c.measurements.artifact_id,c.screenshot.artifact_id)))
    return targets
