DEPENDENCY_TYPES=[
 "PREREQUISITE","DEFINITIONAL","CAUSAL","PROCEDURAL","MATHEMATICAL",
 "CONDITIONAL","CONTEXTUAL","APPLICATION","ADVANCED_EXTENSION"
]
SCOPES=["BOOK_STATED","MODEL_INFERRED","EXTERNAL_HIGHER_KNOWLEDGE"]

def dependency(source,target,dep_type,scope,confidence,evidence_ids=None,reason=None):
    if dep_type not in DEPENDENCY_TYPES: raise ValueError(dep_type)
    if scope not in SCOPES: raise ValueError(scope)
    return {
      "source":source,"target":target,"type":dep_type,"scope":scope,
      "confidence":confidence,"evidence_ids":evidence_ids or [],
      "reason":reason
    }
