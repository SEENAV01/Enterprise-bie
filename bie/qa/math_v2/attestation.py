"""Reuse the existing review trust contract without making a new trust island.

verify_bound checks this MathRequest/MathPolicy digest, exact evidence IDs and
purpose. These receipts certify reviewed mapping/inventory/disclosure only;
they never override failed deterministic mathematics.
"""
from ..reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier

def review_targets(request):
    targets={('inventory','math-scope'):tuple(sorted(c.claim_id for c in request.source.claims))}
    for rows in (request.formulas,request.derivations,request.numericals,request.units):
        for c in rows:
            targets[('mapping',c.case_id)]=tuple(sorted(c.claim_ids))
            if c.condition_claim_ids:targets[('disclosure',c.case_id)]=tuple(sorted(c.condition_claim_ids))
    for c in request.derivations:
        for s in c.steps:targets[('mapping',s.step_id)]=tuple(sorted(s.claim_ids))
    return targets
