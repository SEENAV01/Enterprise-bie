from geometry import intersects
from safe_area import inside_safe_area

def validate_layout(objects,constraints,safe=None):
    errors=[]
    ids={o["object_id"] for o in objects}
    boxes={o["object_id"]:o.get("box",{}) for o in objects}
    for c in constraints:
        for t in c.get("targets",[]):
            if t not in ids: errors.append("LAYOUT_TARGET_MISSING")
    if safe:
        for oid,b in boxes.items():
            if b and not inside_safe_area(b,safe):
                errors.append("OBJECT_OUTSIDE_SAFE_AREA")
    for i,a in enumerate(objects):
        for b in objects[i+1:]:
            ba,bb=boxes.get(a["object_id"]),boxes.get(b["object_id"])
            if ba and bb and intersects(ba,bb,0):
                if a.get("allow_overlap",False) or b.get("allow_overlap",False):
                    continue
                errors.append("OBJECT_OVERLAP")
    return sorted(set(errors))

def solve_layout(composition):
    errors=validate_layout(composition["objects"],
                            composition.get("constraints",[]),
                            composition.get("safe_area"))
    return {"schema_version":"5.39",
            "composition":composition,
            "solver_status":"VALID" if not errors else "NEEDS_REPAIR",
            "errors":errors}
