from .validation_common import *

def validate_spatial(doc):
    issues=[]
    layout=doc.get("layout",{})
    boxes=layout.get("boxes",())
    for i,b in enumerate(boxes):
        vals=[b.get("x"),b.get("y"),b.get("width"),b.get("height")]
        if any(not isinstance(v,(int,float)) or isinstance(v,bool) for v in vals):
            issues.append(issue("BOX_TYPE",f"$.layout.boxes[{i}]","Box values must be numeric"))
            continue
        x,y,w,h=map(float,vals)
        if x<0 or y<0 or w<=0 or h<=0 or x+w>1.0+1e-9 or y+h>1.0+1e-9:
            issues.append(issue("BOX_BOUNDS",f"$.layout.boxes[{i}]","Normalized box outside canvas"))
    constraints=layout.get("relative_constraints",())
    rel={(c.get("subject_id"),c.get("relation"),c.get("reference_id")) for c in constraints}
    opp={"left_of":"right_of","right_of":"left_of","above":"below","below":"above"}
    for i,c in enumerate(constraints):
        r=c.get("relation")
        if r in opp and (c.get("subject_id"),opp[r],c.get("reference_id")) in rel:
            issues.append(issue("CONTRADICTORY_CONSTRAINT",f"$.layout.relative_constraints[{i}]","Contradictory spatial constraint"))
    return report("DSL-VALID-SPATIAL",issues)
