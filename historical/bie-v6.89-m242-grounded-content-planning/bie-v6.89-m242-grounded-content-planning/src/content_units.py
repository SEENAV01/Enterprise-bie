def lesson_unit(unit_id,concept_id,title,role="CORE",prerequisites=None):
    return {"unit_id":unit_id,"concept_id":concept_id,"title":title,"role":role,
            "prerequisites":prerequisites or []}

def build_units(sequence,labels):
    return [lesson_unit(f"LU-{i+1}",c,labels.get(c,c),
                        "PREREQUISITE" if i < len(sequence)-1 else "CORE",
                        sequence[:i]) for i,c in enumerate(sequence)]
