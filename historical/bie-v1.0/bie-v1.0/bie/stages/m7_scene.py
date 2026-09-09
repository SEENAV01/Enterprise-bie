
VISUAL={"definition":"definition_card","process":"process_flow","derivation":"equation_derivation",
        "application":"real_world_context","comparison":"comparison","concept":"explanatory_diagram"}
def run(lesson):
    scenes=[]
    for i,s in enumerate(lesson["sequence"],1):
        kind=s["type"]
        scenes.append({
          "scene_id":f"S{i:02d}","purpose":"application" if kind=="application" else "explain",
          "duration_frames":360,"content_refs":s["refs"],"source_refs":s["source_refs"],
          "visual":{"type":VISUAL.get(kind,"explanatory_diagram"),"layout":"adaptive"},
          "timeline":[{"start":0,"duration":30,"action":"enter"},{"start":30,"duration":330,"action":"teach"}]
        })
    return {"scenes":scenes}
