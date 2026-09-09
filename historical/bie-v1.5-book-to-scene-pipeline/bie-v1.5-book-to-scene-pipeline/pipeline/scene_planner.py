VISUAL_BY_KIND={
 "what":"definition_card",
 "why":"cause_effect",
 "how":"process_sequence",
 "when":"timeline_or_event",
 "where":"map_or_location",
 "who":"entity_context",
 "derivation":"equation_derivation",
 "application":"real_world_application"
}

def plan_scenes(book_ir:dict)->list[dict]:
    scenes=[]
    for u in book_ir["units"]:
        kinds=[]
        for q in u.get("questions",[]):
            if q["kind"] not in kinds: kinds.append(q["kind"])
        for k in kinds:
            scenes.append({
                "scene_id":f'{u["unit_id"]}_{k}',
                "unit_id":u["unit_id"],
                "purpose":f"{k} understanding",
                "question_kind":k,
                "visual_type":VISUAL_BY_KIND.get(k,"explanation"),
                "source_refs":u["passages"],
                "higher_knowledge":u.get("higher_knowledge",[]),
                "status":"PLANNED"
            })
    return scenes
