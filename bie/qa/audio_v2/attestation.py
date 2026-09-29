"""Reuse purpose-scoped review authentication. No runtime keys ship in packages."""
from ..reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier

def review_targets(request,policy):
    targets={('inventory','audio-scope'):tuple(sorted(c.claim_id for c in request.source.claims))}
    clips={c.clip_id:c for c in request.clips};pe={p.clip_id:p for p in request.pronunciation}
    for n in policy.narrations:
        targets[('mapping','script-'+n.clip_id)]=tuple(sorted(n.claim_ids))
        c=clips.get(n.clip_id)
        if c:targets[('calibration','timing-'+n.clip_id)]=tuple(sorted((c.wav.artifact_id,c.timing.artifact_id)))
    for t in policy.terms:
        if t.clip_id in clips and t.clip_id in pe:targets[('mapping','pronunciation-'+t.term_id)]=tuple(sorted((clips[t.clip_id].wav.artifact_id,pe[t.clip_id].artifact.artifact_id)))
    return targets
