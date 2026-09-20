from .validation_common import *

def validate_references(doc):
    issues=[]
    elements=doc.get("elements",())
    tracks=doc.get("tracks",())
    ids=[e.get("element_id") for e in elements]
    if len(ids)!=len(set(ids)):
        issues.append(issue("DUPLICATE_ELEMENT_ID","$.elements","Element IDs must be unique"))
    valid=set(ids)
    tids=[t.get("track_id") for t in tracks]
    if len(tids)!=len(set(tids)):
        issues.append(issue("DUPLICATE_TRACK_ID","$.tracks","Track IDs must be unique"))
    for i,t in enumerate(tracks):
        if t.get("element_id") not in valid:
            issues.append(issue("UNKNOWN_TRACK_ELEMENT",f"$.tracks[{i}].element_id","Track references unknown element"))
    for i,e in enumerate(elements):
        et=e.get("element_type")
        props=e.get("props",{})
        if et in {"annotation","callout"} and props.get("target_element_id") not in valid:
            issues.append(issue("UNKNOWN_TARGET",f"$.elements[{i}].props.target_element_id","Target element does not exist"))
        if et=="highlight":
            for target in props.get("target_element_ids",()):
                if target not in valid:
                    issues.append(issue("UNKNOWN_TARGET",f"$.elements[{i}].props.target_element_ids","Highlight target does not exist"))
    return report("DSL-VALID-REFERENCE",issues)
