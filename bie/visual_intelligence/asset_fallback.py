from .asset_contracts import *
FALLBACKS={"diagram":("vector","textual_callout"),"vector":("diagram","textual_callout"),"map":("diagram","textual_callout"),
"timeline":("diagram","textual_callout"),"graph":("chart","table"),"chart":("table","textual_callout"),
"equation":("textual_callout",),"image":("diagram","textual_callout"),"animation":("diagram","textual_callout")}
def choose_asset_fallback(need,*,failed_kind,reason,available_kinds=()):
    failed=str(failed_kind).strip().lower(); reason=str(reason).strip()
    if not failed or not reason: raise AssetValidationError("failed_kind and reason required")
    allowed=set(str(x).strip().lower() for x in available_kinds if str(x).strip())
    options=FALLBACKS.get(failed,("textual_callout",))
    chosen=next((x for x in options if not allowed or x in allowed),None)
    if chosen is None: return decision(need,"escalate_asset_failure",rationale=("no_safe_fallback",f"reason={reason}"))
    return decision(need,"use_asset_fallback",request={"fallback_kind":chosen,"failed_kind":failed,"reason":reason,"preserve_required_semantics":True},
                    rationale=(f"fallback={chosen}","review_required"))
