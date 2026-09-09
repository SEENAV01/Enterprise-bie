from scene_types import scene

TYPE_MAP={
"CONTEXT":"EXPLANATION","RECAP":"RECAP","DEFINITION":"DEFINITION",
"INTUITION":"DIAGRAM","MECHANISM":"PROCESS","DERIVATION_STEP":"DERIVATION",
"WORKED_EXAMPLE":"WORKED_EXAMPLE","APPLICATION":"APPLICATION",
"COMPARISON":"COMPARISON","QUESTION":"QUESTION","TRANSFER":"APPLICATION"
}

def compile_scenes(script_units):
    scenes=[]
    for i,u in enumerate(script_units,1):
        typ=TYPE_MAP.get(u["type"],"EXPLANATION")
        scenes.append(scene(
          f"s{i}",typ,u["objective"],[u["id"]],u.get("evidence_ids",[])
        ))
    return scenes
