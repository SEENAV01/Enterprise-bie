
VISUAL_MAP = {
 "definition":"definition_card",
 "process":"process_flow",
 "mechanism":"mechanism_animation",
 "cause_effect":"causal_diagram",
 "derivation":"equation_derivation",
 "comparison":"comparison",
 "timeline":"timeline",
 "data":"animated_chart",
 "simulation":"parameter_simulation",
 "application":"real_world_context",
 "question":"interactive_question",
 "summary":"concept_map"
}

def choose_visual(kind, purpose=None):
    return VISUAL_MAP.get(kind, "explanatory_diagram")

def make_scene(unit, frame_rate=30, seconds=12):
    kind=unit.get("kind","concept")
    purpose=unit.get("purpose") or kind
    visual=choose_visual(kind,purpose)
    frames=max(1,int(seconds*frame_rate))
    return {
      "scene_id":f"S_{unit['id']}",
      "purpose":purpose if purpose in {"explain","define","process","cause_effect","derivation","compare","timeline","data","simulation","application","question","summary"} else "explain",
      "duration_frames":frames,
      "content_refs":[unit["id"]],
      "visual":{"type":visual,"layout":"adaptive"},
      "narration":{"text":unit.get("narration",""),"source_refs":unit.get("source_refs",[])},
      "timeline":[
        {"start":0,"duration":min(30,frames),"action":"enter"},
        {"start":min(30,frames),"duration":max(1,frames-min(30,frames)),"action":"teach"}
      ],
      "elements":unit.get("elements",[]),
      "source_refs":unit.get("source_refs",[])
    }

def compile_scene_to_remotion(scene):
    # Produces an intermediate deterministic representation, not arbitrary AI-generated React.
    return {
      "component":"BIEScene",
      "props":{
        "sceneId":scene["scene_id"],
        "visualType":scene["visual"]["type"],
        "durationInFrames":scene["duration_frames"],
        "contentRefs":scene["content_refs"],
        "timeline":scene["timeline"],
        "elements":scene["elements"],
        "narration":scene["narration"]
      }
    }

def compile_lesson(lesson):
    scenes=[]
    for step in lesson.get("sequence",[]):
        ref=(step.get("refs") or ["unknown"])[0]
        unit={"id":ref,"kind":step.get("type","concept"),
              "purpose":"application" if step.get("type")=="application" else "explain",
              "source_refs":step.get("source_refs",[])}
        scenes.append(make_scene(unit))
    return scenes
