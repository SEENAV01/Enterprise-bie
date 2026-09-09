def classify_claim(source_supported:bool, external_requested:bool=False)->str:
    if source_supported and not external_requested:
        return "SOURCE_DERIVED"
    if external_requested:
        return "EXTERNAL_RESEARCH_REQUIRED"
    return "UNSUPPORTED_DO_NOT_ASSERT"

def correction_policy(source_text:str, proposed_correction:str)->dict:
    return {
        "source_text":source_text,
        "proposed_correction":proposed_correction,
        "action":"REVIEW",
        "reason":"Do not silently replace source wording."
    }
