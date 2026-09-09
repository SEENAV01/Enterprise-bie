from assets import plan_assets
from style import visual_style,style_constraints
from voice import select_voice,narration_spec
from scene import scene,validate_scene

def build_scene_runtime():
    preferences={"language":"hi","pace":"adaptive","visual_density":"low",
                  "high_contrast":True,"reduced_motion":True,"voice":"clear"}
    accessibility={"captions":True,"audio_description":True,
                   "high_contrast":True,"reduced_motion":True}
    requirements=[
      {"asset_type":"DIAGRAM","role":"concept_visual","description":"Electric field diagram",
       "accessibility":{"captions":True}},
      {"asset_type":"TEXT","role":"key_definition","description":"Key definition",
       "accessibility":{"high_contrast":True}}]
    assets=plan_assets("scene-01",requirements)
    style=visual_style({**preferences,**accessibility})
    voice=select_voice(preferences)
    narration=narration_spec(voice,accessibility)
    s=scene("scene-01","Electric Field",assets,style,narration,accessibility)
    validation=validate_scene(s)
    return {"schema_version":"6.82","scene":s,"asset_plan":assets,
            "style_constraints":style_constraints(style),"voice":voice,
            "narration_spec":narration,"validation":validation,
            "scene_generation_gate":{"valid":validation["passed"] and
                bool(assets) and bool(narration["voice"]),"errors":[]}}
