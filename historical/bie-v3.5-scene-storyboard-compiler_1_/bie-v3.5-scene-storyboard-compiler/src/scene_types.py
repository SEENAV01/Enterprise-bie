SCENE_TYPES=[
"TITLE","EXPLANATION","DEFINITION","DIAGRAM","PROCESS","EQUATION",
"DERIVATION","WORKED_EXAMPLE","APPLICATION","COMPARISON","QUESTION",
"RECAP","TRANSITION","PAUSE","SUMMARY"
]

def scene(scene_id, scene_type, objective, narration_unit_ids, evidence_ids=None):
    return {
      "scene_id":scene_id,
      "scene_type":scene_type,
      "objective":objective,
      "narration_unit_ids":narration_unit_ids,
      "evidence_ids":evidence_ids or [],
      "duration_policy":"AUDIO_DRIVEN",
      "visual_elements":[],
      "animation_events":[],
      "camera_events":[],
      "transition":None,
      "sync_anchors":[]
    }
