from grounding import assess_all
from coverage import coverage

def compile_grounded_content(source_id,evidence,claims,video_elements):
    assessments=assess_all(claims,evidence)
    errors=[]
    for a in assessments:
        if a["status"] in ("UNSUPPORTED","MISSING_EVIDENCE","REASONING_REQUIRED"):
            c=next(x for x in claims if x["claim_id"]==a["claim_id"])
            if c.get("required",True):
                errors.append({"claim_id":a["claim_id"],"status":a["status"]})
    return {
      "schema_version":"5.3",
      "source_id":source_id,
      "evidence":evidence,
      "claims":claims,
      "claim_assessments":assessments,
      "video_elements":video_elements,
      "coverage":coverage(claims),
      "quality_gate":{"valid":not errors,"errors":errors}
    }
