def stage_for_scene(s):
    typ=s["scene_type"]
    presets={
      "DEFINITION":["heading","definition_text","key_term_highlight"],
      "DIAGRAM":["diagram_canvas","labels","relationship_highlights"],
      "PROCESS":["system_elements","step_sequence","active_step_highlight"],
      "EQUATION":["equation","term_highlights","derivation_pointer"],
      "DERIVATION":["equation_line","step_marker","transformation_highlight"],
      "WORKED_EXAMPLE":["problem","given_data","step_solution","answer"],
      "APPLICATION":["real_world_context","concept_overlay","mechanism_callout"],
      "QUESTION":["question_text","response_area"],
      "RECAP":["key_points","relationship_map"],
      "EXPLANATION":["heading","supporting_visual","key_phrase"]
    }
    s["visual_elements"]=presets.get(typ,["heading","supporting_visual"])
    return s
