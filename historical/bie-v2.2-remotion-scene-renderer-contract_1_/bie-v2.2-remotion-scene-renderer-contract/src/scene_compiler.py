from scene_schema import validate_scene

def narration_timing(text, words_per_minute=145):
    words=max(1,len(text.split()))
    return int((words/words_per_minute)*60_000)

def compile_unit(unit):
    scenes=[]
    for i,s in enumerate(unit.get("scenes",[]),1):
        text=s.get("narration","")
        duration=max(2500,narration_timing(text) if text else 3000)
        scenes.append({
            "scene_id":f'{unit["unit_id"]}_S{i:02d}',
            "type":s["type"],
            "duration_ms":duration,
            "objective":s.get("objective",unit.get("objective","")),
            "visual":{
                "type":s.get("visual_type","mixed"),
                "instructions":s.get("visual_instructions",""),
                "assets":s.get("assets",[])
            },
            "narration":text,
            "on_screen_text":s.get("on_screen_text",[]),
            "equations":s.get("equations",[]),
            "animation":s.get("animation",{"enter":"fade","exit":"fade","actions":[]}),
            "camera":s.get("camera",{"mode":"static"}),
            "transition":s.get("transition","cut"),
            "emphasis":s.get("emphasis",[]),
            "evidence_refs":unit.get("evidence_refs",[]),
            "checkpoint":s.get("checkpoint")
        })
    return scenes

def compile_lesson(lesson):
    output=[]
    for u in lesson.get("learning_units",[]):
        for s in compile_unit(u):
            errors=validate_scene(s)
            if errors: raise ValueError(f'{s.get("scene_id")}: {errors}')
            output.append(s)
    return {
        "schema_version":"2.2",
        "renderer":"remotion",
        "fps":30,
        "resolution":{"width":1920,"height":1080},
        "scenes":output
    }
