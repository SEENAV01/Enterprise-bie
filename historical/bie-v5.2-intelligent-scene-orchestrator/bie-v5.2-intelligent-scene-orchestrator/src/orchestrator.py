from layout_engine import auto_layout,collision_report
from focus import focus_plan
from cognitive_load import recommend
from animation_orchestrator import coordinate

def orchestrate(scene,active_ids=None):
    active_ids=active_ids or []
    placed=auto_layout(scene.get("objects",[]),
                       scene.get("canvas_width",1920),
                       scene.get("canvas_height",1080))
    collisions=collision_report(placed)
    focus=focus_plan(placed,active_ids)
    load=recommend({"objects":placed})
    events=coordinate(scene.get("events",[]))
    return {
      "scene_id":scene["scene_id"],
      "objects":placed,
      "focus_plan":focus,
      "animation_plan":events,
      "collisions":collisions,
      "cognitive_load":load,
      "policy":{
        "avoid_occlusion":True,
        "attention_is_managed":True,
        "semantic_priority_over_decoration":True
      }
    }
