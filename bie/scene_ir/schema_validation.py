from .validation_common import *

REQUIRED={
 "scene_id":str,"schema_version":str,"title":str,"duration_ms":int,
 "elements":(list,tuple),"tracks":(list,tuple),
 "source_refs":(list,tuple),"reasoning_refs":(list,tuple),
}

def validate_schema_shape(doc):
    issues=[]
    if not isinstance(doc,dict):
        return report("DSL-VALID-SCHEMA", [issue("ROOT_TYPE","$","Scene IR root must be an object")])
    for key,typ in REQUIRED.items():
        if key not in doc:
            issues.append(issue("MISSING_FIELD","$."+key,f"Required field {key} missing"))
        elif not isinstance(doc[key],typ) or (typ is int and isinstance(doc[key],bool)):
            issues.append(issue("TYPE_MISMATCH","$."+key,f"{key} has invalid type"))
    if isinstance(doc.get("duration_ms"),int) and not isinstance(doc.get("duration_ms"),bool) and doc["duration_ms"]<1:
        issues.append(issue("INVALID_DURATION","$.duration_ms","duration_ms must be >=1"))
    if doc.get("schema_version")!="1.0.0":
        issues.append(issue("SCHEMA_VERSION","$.schema_version","Unsupported schema version"))
    if not doc.get("elements"):
        issues.append(issue("EMPTY_ELEMENTS","$.elements","At least one element required"))
    return report("DSL-VALID-SCHEMA",issues)
