from .asset_contracts import *
ALLOWED={"diagram","vector","map","timeline","graph","chart","equation","animation"}
def request_generated_asset(need,*,media_kind,prompt_spec,deterministic_seed=None):
    kind=str(media_kind).strip().lower()
    if kind not in ALLOWED or kind not in need.media_kinds: raise AssetValidationError("media kind not allowed")
    spec=dict(prompt_spec)
    if not spec: raise AssetValidationError("prompt_spec required")
    if {"unverified_fact","fabricate_source","invent_data"}&set(map(str,spec)): raise AssetValidationError("ungrounded instruction")
    req={"media_kind":kind,"prompt_spec":spec,"deterministic_seed":deterministic_seed,
         "evidence_refs":list(need.evidence_refs),"reasoning_refs":list(need.reasoning_refs),
         "requires_post_generation_grounding_check":True}
    return decision(need,"request_generated_asset",request=req,rationale=("generation_needed","grounding_check_required"))
