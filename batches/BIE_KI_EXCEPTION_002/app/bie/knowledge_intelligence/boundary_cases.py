class E(ValueError):pass
def make(c,case,behavior,anchor):
 if not c or not str(case).strip() or not str(behavior).strip() or not anchor:raise E("boundary")
 return {"concept_id":c,"case":case.strip(),"expected_behavior":behavior.strip(),"anchor_id":anchor,"type":"BOUNDARY_CASE"}
