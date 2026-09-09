def validate_extractions(extractions):
    errors=[]; warnings=[]
    for x in extractions:
        if x.get("dimension") not in [
          "WHAT","WHY","HOW","WHEN","WHERE","WHO","DEFINITION","PROCESS",
          "CAUSE","DERIVATION","EXAMPLE","APPLICATION","ASSUMPTION",
          "EXCEPTION","EVIDENCE","PREREQUISITE","DEPENDENCY","COMPARISON",
          "LIMITATION","COUNTEREXAMPLE","SEQUENCE","MECHANISM","FORMULA",
          "OBSERVATION","CONCLUSION"]:
            errors.append("UNKNOWN_DIMENSION")
        if not x.get("source_span"):
            errors.append("MISSING_SOURCE_SPAN")
        if not x.get("text"):
            errors.append("EMPTY_EXTRACTION")
        if x.get("confidence")=="CANDIDATE":
            warnings.append("CANDIDATE_REQUIRES_REVIEW")
    return {"valid":not errors,"errors":errors,"warnings":warnings}
