"""Reuse content-bound, purpose-scoped review trust; no signing keys are shipped."""
from ..reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier

def review_targets(request,policy):
    targets={('inventory','animation-scope'):tuple(sorted(t.track_id for t in request.tracks))}
    for t in policy.tracks:targets[('mapping',t.track_id)]=tuple(sorted(t.claim_ids))
    for c in policy.cues:targets[('disclosure',c.cue_id)]=tuple(sorted(c.claim_ids))
    for r in policy.invariants:targets[('inference',r.invariant_id)]=tuple(sorted(r.track_ids))
    return targets
