MEDIA_FOR_MODE={
"EXPLAIN":["TEXT","DIAGRAM","HIGHLIGHT"],
"EXPLAIN_WITH_CAUSAL_MODEL":["DIAGRAM","ANIMATION","HIGHLIGHT"],
"DEMONSTRATE_PROCESS":["ANIMATION","DIAGRAM","HIGHLIGHT"],
"DERIVE_STEP_BY_STEP":["EQUATION","HIGHLIGHT","TEXT"],
"DERIVE_OR_VISUALIZE":["EQUATION","ANIMATION","HIGHLIGHT"],
"SHOW_APPLICATION":["SCENARIO","DIAGRAM","TEXT"],
"SHOW_EXAMPLE":["EXAMPLE","EQUATION","HIGHLIGHT"],
"COMPARE":["COMPARISON","HIGHLIGHT"],
"COUNTEREXAMPLE":["EXAMPLE","HIGHLIGHT"],
"CONTEXTUALIZE":["TIMELINE_OR_MAP","TEXT"]
}

def visual_intent(mode):
    return MEDIA_FOR_MODE.get(mode,["TEXT","DIAGRAM"])

def build_visual_plan(blocks,units_by_id):
    out=[]
    for b in blocks:
        for kid in b.get("knowledge_ids",[]):
            u=units_by_id.get(kid,{})
            out.append({
              "block_id":b["id"],
              "knowledge_id":kid,
              "visual_intent":visual_intent(u.get("teaching_mode","EXPLAIN")),
              "must_explain_before_showing":True
            })
    return out
