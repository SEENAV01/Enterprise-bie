from .asset_contracts import *
ROLE_DEFAULTS={"diagram":("diagram","vector"),"map":("map","image"),"timeline":("timeline","vector"),
"graph":("graph","chart"),"equation":("equation","vector"),"process":("diagram","animation"),
"comparison":("chart","diagram"),"context":("image",)}
def detect_asset_need(*,need_id,semantic_role,evidence_refs,reasoning_refs,representation=None,required=True,priority=50,constraints=None,confidence_score=1.0):
    role=str(semantic_role).strip().lower()
    if not role: raise AssetValidationError("semantic_role")
    rep=(representation or role).strip().lower()
    if rep not in ROLE_DEFAULTS: raise AssetValidationError(f"unsupported representation: {rep}")
    return AssetNeed(need_id,role,ROLE_DEFAULTS[rep],tuple(evidence_refs),tuple(reasoning_refs),bool(required),priority,dict(constraints or {}),conf(confidence_score))
