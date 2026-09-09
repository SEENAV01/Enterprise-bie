def course_continuity(course_id, style_id, grammar_id,
                     asset_ids, motion_rule_ids):
    return {
      "course_id":course_id,"style_id":style_id,
      "visual_grammar_id":grammar_id,
      "asset_ids":asset_ids,
      "motion_rule_ids":motion_rule_ids
    }

def continuity_diff(previous,current):
    diffs=[]
    for k in ("style_id","visual_grammar_id"):
        if previous.get(k)!=current.get(k):
            diffs.append({"field":k,"from":previous.get(k),"to":current.get(k)})
    return diffs
