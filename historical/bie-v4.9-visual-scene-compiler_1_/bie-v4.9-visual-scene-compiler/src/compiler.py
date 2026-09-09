from scene_builder import build_scene
from scene_validator import validate_scene
from accessibility import accessibility_spec
from animation_policy import motion_limits

def compile_visual_scenes(timeline, event_map):
    scenes=[]
    for s in timeline.get("scenes",[]):
        ev=[e for e in event_map if
            s["start_s"]<=e.get("time_s",0)<=s["end_s"]]
        scene_events=[]
        for e in ev:
            scene_events.append({
              "event_id":e["event_id"],
              "kind":e.get("kind","TEXT"),
              "content":e.get("content",""),
              "animation":e.get("animation","APPEAR"),
              "region_id":e.get("region_id","main")
            })
        sc=build_scene(s,scene_events)
        sc["validation"]=validate_scene(sc)
        scenes.append(sc)
    return {
      "schema_version":"4.9",
      "fps":timeline.get("fps",30),
      "duration_s":timeline["duration_s"],
      "scenes":scenes,
      "accessibility":accessibility_spec(),
      "motion_policy":motion_limits(),
      "renderer":"RENDERER_NEUTRAL"
    }
