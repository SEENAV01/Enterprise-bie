ERROR_TYPES={
    "DEFINITION_CONFUSION","FORMULA_SELECTION","UNIT_ERROR",
    "SIGN_DIRECTION","CAUSAL_REASONING","PREREQUISITE_GAP","CALCULATION"
}
def classify_error(question,expected,actual):
    if actual==expected: return {"type":"NONE","severity":0}
    hint=question.get("error_hint")
    return {"type":hint if hint in ERROR_TYPES else "CONCEPTUAL_ERROR","severity":1}
