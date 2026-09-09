DIMENSIONS=[
"WHAT","WHY","HOW","WHEN","WHERE","WHO",
"DEFINITION","PROCESS","CAUSE","DERIVATION","EXAMPLE",
"APPLICATION","ASSUMPTION","EXCEPTION","EVIDENCE",
"PREREQUISITE","DEPENDENCY","COMPARISON","LIMITATION",
"COUNTEREXAMPLE","SEQUENCE","MECHANISM","FORMULA",
"OBSERVATION","CONCLUSION"
]

def extraction(item_id, source_span, dimension, text,
               confidence="CANDIDATE", evidence_ids=None, relations=None):
    return {
      "id":item_id,
      "source_span":source_span,
      "dimension":dimension,
      "text":text,
      "confidence":confidence,
      "evidence_ids":evidence_ids or [],
      "relations":relations or []
    }
