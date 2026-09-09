def representation_spec(spec_id,representation_type,
                        content_refs=None,objective_refs=None,
                        pedagogical_purpose=None,requirements=None):
    return {"spec_id":spec_id,"representation_type":representation_type,
            "content_refs":content_refs or [],
            "objective_refs":objective_refs or [],
            "pedagogical_purpose":pedagogical_purpose,
            "requirements":requirements or {}}

def representation_types():
    return ["TEXT","DIAGRAM","ANIMATION","SIMULATION","INTERACTIVE",
            "NARRATION","EQUATION","TABLE","CHART","EXAMPLE",
            "ASSESSMENT","MIXED"]
