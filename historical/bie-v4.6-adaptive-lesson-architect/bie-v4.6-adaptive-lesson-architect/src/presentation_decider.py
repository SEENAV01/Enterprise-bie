MODES={
"DEFINITION":["NARRATE","TEXT","DIAGRAM"],
"EXPLAIN":["NARRATE","DIAGRAM","TEXT"],
"EXPLAIN_WITH_CAUSAL_MODEL":["NARRATE","ANIMATION","DIAGRAM"],
"DEMONSTRATE_PROCESS":["NARRATE","ANIMATION","DIAGRAM"],
"DERIVE_STEP_BY_STEP":["NARRATE","EQUATION","HIGHLIGHT"],
"DERIVE_OR_VISUALIZE":["NARRATE","EQUATION","ANIMATION"],
"SHOW_APPLICATION":["NARRATE","SCENARIO","DIAGRAM"],
"SHOW_EXAMPLE":["NARRATE","WORKED_STEPS","HIGHLIGHT"],
"COMPARE":["NARRATE","COMPARISON_TABLE","DIAGRAM"],
"COUNTEREXAMPLE":["NARRATE","COUNTEREXAMPLE","HIGHLIGHT"],
"CONTEXTUALIZE":["NARRATE","TIMELINE_OR_MAP","TEXT"]
}

def decide(mode):
    return MODES.get(mode,["NARRATE","TEXT"])

def presentation_plan(blocks, units_by_id):
    plans=[]
    for b in blocks:
        for kid in b.get("knowledge_ids",[]):
            u=units_by_id.get(kid,{})
            plans.append({
              "block_id":b["id"],"knowledge_id":kid,
              "media":decide(u.get("teaching_mode","EXPLAIN"))
            })
    return plans
