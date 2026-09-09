VALID={"left_of","right_of","above","below","inside","contains","overlaps","adjacent","intersects","disjoint"}
def relation(subject,relation,obj,evidence):
 if not subject.strip() or not obj.strip() or relation not in VALID or not evidence:raise ValueError("grounded spatial relation required")
 if subject==obj and relation in {"left_of","right_of","above","below","disjoint"}:raise ValueError("invalid self relation")
 return (subject,relation,obj,tuple(evidence))
