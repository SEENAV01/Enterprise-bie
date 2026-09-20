from .access_contracts import *

ROLE_MIN_PX={"title":36,"heading":28,"body":22,"caption":18,"label":18,"annotation":18,"equation":24,"prompt":22}

def evaluate_readable_size(intent, *, font_px, viewport_width_px, viewing_scale=1.0, dense_mode=False):
    px=finite(font_px,field_name="font_px")
    vw=finite(viewport_width_px,field_name="viewport_width_px")
    scale=finite(viewing_scale,field_name="viewing_scale")
    if px<=0 or vw<240 or scale<=0: raise ReadabilityError("invalid size/view parameters")
    baseline=ROLE_MIN_PX.get(intent.semantic_role,20)
    if dense_mode: baseline=max(16,baseline-2)
    effective=px*scale
    passed=effective+1e-9>=baseline
    relative=px/vw
    warnings=[]
    if relative<0.012: warnings.append("small_relative_to_viewport")
    if not passed: warnings.append("below_role_minimum")
    return decision(intent,action="readable_size_pass" if passed else "increase_text_size",
                    payload={"font_px":px,"effective_px":round(effective,3),"role_min_px":baseline,
                             "viewport_width_px":vw,"relative_width":round(relative,6),"passes":passed},
                    rationale=(f"effective_px={effective:.2f}",f"role_min_px={baseline}"),warnings=warnings)
