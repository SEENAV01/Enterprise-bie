UNIT_TYPES=[
"HOOK","CONTEXT","EXPLANATION","DEFINITION","INTUITION","MECHANISM",
"DERIVATION_STEP","WORKED_EXAMPLE","APPLICATION","COMPARISON",
"MISCONCEPTION","QUESTION","ANSWER","RECAP","TRANSFER","TRANSITION"
]

def unit(unit_id, unit_type, objective, text, evidence_ids=None, visual_intent=None):
    return {
      "id":unit_id,"type":unit_type,"objective":objective,"text":text,
      "evidence_ids":evidence_ids or [],
      "visual_intent":visual_intent,
      "delivery":"NARRATION_OR_ONSCREEN"
    }
