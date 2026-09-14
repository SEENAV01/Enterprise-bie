from .contract_validation import nonblank,items,ids,finite
from dataclasses import dataclass
@dataclass(frozen=True)
class VoiceoverDraft: segment_id:str; text:str; evidence_ids:tuple[str,...]; unsupported_claims:tuple[str,...]; requires_review:bool
def generate_voiceover(segment_id,claims,evidence_by_claim,style="clear"):
    nonblank(segment_id,"segment"); nonblank(style,"style")
    claims=items(claims,"claims")
    if not isinstance(evidence_by_claim,dict): raise ValueError("claim evidence mapping required")
    for claim in claims: nonblank(claim,"claim text")
    supported=[]; unsupported=[]
    for c in claims:
        ev=ids(evidence_by_claim.get(c,()),"claim evidence",required=False,canonical=True)
        if ev:supported.append((c,ev))
        else:unsupported.append(c)
    text=" ".join(c for c,_ in supported); evidence=tuple(sorted({e for _,ev in supported for e in ev}))
    return VoiceoverDraft(segment_id,text,evidence,tuple(unsupported),bool(unsupported))
