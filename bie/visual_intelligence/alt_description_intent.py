from .access_contracts import *
from dataclasses import dataclass

DECORATIVE_ROLES={"decorative","background"}
COMPLEX_ROLES={"diagram","map","chart","graph","timeline","equation","process","simulation"}

@dataclass(frozen=True)
class AltDescriptionIntent:
    intent_id:str
    mode:str
    purpose:str
    must_include:tuple[str,...]
    avoid:tuple[str,...]
    evidence_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    review_required:bool=True
    accepted:bool=False

def build_alt_description_intent(intent, *, purpose, key_elements=(), decorative=False):
    purpose=token(purpose,field_name="purpose")
    elems=ids(key_elements,field_name="key_elements",allow_empty=True)
    role=intent.semantic_role
    if decorative or role in DECORATIVE_ROLES:
        mode="empty_alt"
        must=()
        avoid=("do_not_describe_decorative_detail",)
    elif role in COMPLEX_ROLES:
        if not elems:
            raise AltIntentError("complex visual requires key_elements")
        mode="long_description"
        must=elems
        avoid=("do_not_invent_unseen_facts","do_not_repeat_caption_verbatim")
    else:
        mode="concise_alt"
        must=elems
        avoid=("do_not_invent_unseen_facts",)
    return AltDescriptionIntent(intent.intent_id,mode,purpose,must,avoid,intent.evidence_refs,intent.reasoning_refs,True,False)

def as_decision(intent, alt):
    return decision(intent,action="alt_description_intent",
                    payload={"mode":alt.mode,"purpose":alt.purpose,"must_include":list(alt.must_include),"avoid":list(alt.avoid)},
                    rationale=(f"mode={alt.mode}",))
