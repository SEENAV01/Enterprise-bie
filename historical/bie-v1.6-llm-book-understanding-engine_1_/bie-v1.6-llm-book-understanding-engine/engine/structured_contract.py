import json

QUESTION_TYPES=["what","why","how","when","where","who","derivation","application"]

def empty_unit(unit_id,title,source_refs):
    return {
      "unit_id":unit_id,"title":title,"source_refs":source_refs,
      "claims":[],
      "question_matrix":{k:[] for k in QUESTION_TYPES},
      "definitions":[],"processes":[],"causes":[],
      "time_place":[],"people_entities":[],"applications":[],
      "derivations":[],"higher_knowledge_candidates":[],
      "dependencies":[],"uncertainties":[],"confidence":0.0,
      "review_required":True
    }

def validate_unit(u):
    required=["unit_id","title","source_refs","claims","question_matrix",
              "definitions","processes","causes","applications",
              "dependencies","uncertainties","confidence","review_required"]
    missing=[k for k in required if k not in u]
    if missing: return False,{"error":"MISSING_FIELDS","fields":missing}
    if not (0<=float(u["confidence"])<=1): return False,{"error":"BAD_CONFIDENCE"}
    if not u["source_refs"]: return False,{"error":"NO_SOURCE_REF"}
    return True,{"status":"OK"}
