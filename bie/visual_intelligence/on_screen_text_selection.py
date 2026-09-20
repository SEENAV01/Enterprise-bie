from .text_contracts import *
ALLOWED_ROLES={"title","heading","definition","key_point","equation","label","annotation","caption","prompt","warning","summary"}
def select_on_screen_text(intent, *, available_char_budget=180, allow_condense=True):
    if intent.role not in ALLOWED_ROLES:
        raise TextVisualValidationError(f"unsupported on-screen text role: {intent.role}")
    if isinstance(available_char_budget,bool) or not isinstance(available_char_budget,int) or available_char_budget<1:
        raise TextVisualValidationError("available_char_budget must be positive integer")
    limit=min(intent.max_chars,available_char_budget)
    text=" ".join(intent.text.split())
    if len(text)<=limit:
        return decision(intent,action="show_text",display_text=text,rationale=("within_budget",))
    if not allow_condense:
        if intent.required:
            return decision(intent,action="escalate_text_overflow",display_text=text,rationale=("required_text_exceeds_budget",),
                            warnings=("needs_layout_or_script_revision",))
        return decision(intent,action="omit_optional_text",display_text="",rationale=("optional_text_exceeds_budget",))
    if limit<8:
        return decision(intent,action="escalate_text_overflow",display_text=text,rationale=("budget_too_small_to_condense",))
    condensed=text[:limit-1].rstrip()+"…"
    return decision(intent,action="show_condensed_text",display_text=condensed,
                    rationale=(f"original_chars={len(text)}",f"display_chars={len(condensed)}"),
                    warnings=("condensed_for_display",))
