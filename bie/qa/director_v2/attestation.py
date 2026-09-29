"""Use existing purpose-scoped PR/RE trust management; never embed operational keys."""
from ..reasoning_v2.attestation import Review, ReviewKey, ReviewVerifier


def review_targets(request):
    out = {('inventory', 'director-scope'): tuple(sorted(c.claim_id for c in request.source.claims)),
           ('teaching', 'pacing-profile'): ('pacing-profile',)}
    for s in request.scenes:
        out[('teaching', s.scene_id)] = tuple(sorted(s.objective_ids))
    spoken = {x.beat_id: x for x in request.spoken_forms}
    for b in request.beats:
        extra = spoken[b.beat_id].claim_ids if b.beat_id in spoken else ()
        out[('mapping', b.beat_id)] = tuple(sorted(set((b.beat_id,) + b.claim_ids + extra)))
    for r in request.routes: out[('inventory', r.route_id)] = tuple(sorted(r.scene_ids))
    for t in request.transitions: out[('inference', t.transition_id)] = tuple(sorted(t.claim_ids))
    for p in request.promises: out[('teaching', p.promise_id)] = tuple(sorted(set((p.setup_beat_id,) + p.payoff_beat_ids)))
    for t in request.term_introductions: out[('teaching', t.introduction_id)] = (t.beat_id,)
    for f in request.fidelity:
        out[('support', f.mapping_id)] = tuple(sorted(set((f.claim_id,) + f.citation_ids + f.disclosure_claim_ids + tuple(c.claim_id for c in f.conditions))))
    # Expanded speech is included in the whole request digest and beat mapping review.
    return out
