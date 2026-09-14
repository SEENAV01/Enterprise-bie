from dataclasses import dataclass
@dataclass(frozen=True)
class VoiceoverDraft: segment_id:str; text:str; evidence_ids:tuple[str,...]; unsupported_claims:tuple[str,...]; requires_review:bool
def generate_voiceover(segment_id,claims,evidence_by_claim,style="clear"):
    if not segment_id.strip(): raise ValueError("segment")
    supported=[]; unsupported=[]
    for c in claims:
        ev=tuple(sorted(set(evidence_by_claim.get(c,()))))
        if ev:supported.append((c,ev))
        else:unsupported.append(c)
    text=" ".join(c for c,_ in supported); evidence=tuple(sorted({e for _,ev in supported for e in ev}))
    return VoiceoverDraft(segment_id,text,evidence,tuple(unsupported),bool(unsupported))
