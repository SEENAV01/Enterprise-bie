from .text_contracts import *
ALLOWED_ALIGN={"left","center","right"}
def equation_typography(intent, *, display_mode=True, font_scale=1.0, align="center", max_lines=3):
    if intent.role!="equation": raise TextVisualValidationError("equation typography requires role=equation")
    fs=finite(font_scale,field_name="font_scale")
    if fs<0.5 or fs>2.0: raise TextVisualValidationError("font_scale must be in [0.5,2]")
    if align not in ALLOWED_ALIGN: raise TextVisualValidationError("unsupported equation alignment")
    if isinstance(max_lines,bool) or not isinstance(max_lines,int) or max_lines<1 or max_lines>8:
        raise TextVisualValidationError("max_lines must be integer in [1,8]")
    text=intent.text.strip()
    if "$$" in text and not display_mode:
        raise TextVisualValidationError("display-delimited equation cannot be forced inline")
    warnings=("equation_may_overflow_single_line",) if len(text)>120 and max_lines==1 else ()
    style={"display_mode":bool(display_mode),"font_scale":fs,"align":align,"max_lines":max_lines,
           "math_semantics_preserved":True,"plain_text_fallback_required":True}
    return decision(intent,action="typeset_equation",style=style,rationale=("semantic_math_typography",),warnings=warnings)
