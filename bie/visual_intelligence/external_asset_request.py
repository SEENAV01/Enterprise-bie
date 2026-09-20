from .asset_contracts import *
def request_external_asset(need,*,media_kind,query_terms,allowed_domains=(),require_rights_metadata=True):
    kind=str(media_kind).strip().lower()
    if kind not in need.media_kinds: raise AssetValidationError("media kind not allowed")
    terms=tuple(str(x).strip() for x in query_terms if str(x).strip())
    if not terms: raise AssetValidationError("query_terms required")
    domains=tuple(sorted(set(str(x).strip().lower() for x in allowed_domains if str(x).strip())))
    req={"media_kind":kind,"query_terms":list(terms),"allowed_domains":list(domains),
         "require_rights_metadata":bool(require_rights_metadata),"evidence_refs":list(need.evidence_refs),
         "reasoning_refs":list(need.reasoning_refs),"selection_must_be_reviewed":True}
    return decision(need,"request_external_asset",request=req,rationale=("external_search_required",))
