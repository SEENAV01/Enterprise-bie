def diagnosis(diagnosis_id,check_ref,error_type,severity,
              evidence=None,likely_causes=None,confidence=None):
    return {"diagnosis_id":diagnosis_id,"check_ref":check_ref,
            "error_type":error_type,"severity":severity,
            "evidence":evidence or [],
            "likely_causes":likely_causes or [],
            "confidence":confidence}

def error_types():
    return ["SOURCE","CONTENT","PEDAGOGY","REPRESENTATION",
            "TIMING","AUDIO","VISUAL","INTERACTION",
            "ACCESSIBILITY","RENDERER","CONTRACT","SYSTEM"]
