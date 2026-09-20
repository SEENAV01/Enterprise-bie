from .access_contracts import *

ALLOWED_SECONDARY={"shape","pattern","icon","label","position","line_style","texture","symbol","value_text"}

def evaluate_color_independent_encoding(intent, *, categories, color_map, secondary_encodings):
    cats=tuple(token(c,field_name="category") for c in categories)
    if not cats: raise EncodingError("categories required")
    if len(set(cats))!=len(cats): raise EncodingError("duplicate categories")
    if set(color_map)!=set(cats): raise EncodingError("color_map must cover categories exactly")
    missing=[]
    normalized={}
    for c in cats:
        enc=tuple(sorted(set(str(x).strip().lower() for x in secondary_encodings.get(c,()) if str(x).strip())))
        bad=set(enc)-ALLOWED_SECONDARY
        if bad: raise EncodingError(f"unsupported secondary encoding: {sorted(bad)}")
        normalized[c]=enc
        if not enc: missing.append(c)
    passed=not missing
    return decision(intent,action="color_independent_pass" if passed else "add_noncolor_encoding",
                    payload={"categories":list(cats),"color_map":dict(color_map),
                             "secondary_encodings":normalized,"missing_secondary":missing,"passes":passed},
                    rationale=("all_categories_have_noncolor_channel",) if passed else ("color_only_information_detected",),
                    warnings=() if passed else ("color_only_encoding",))
