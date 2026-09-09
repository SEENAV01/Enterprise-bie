from frame_timing import seconds_to_frames
from render_manifest import build_manifest
from incremental import changed_scenes
from qa import qa_scene,course_qa
from repair import repair_actions

def prepare_render(scenes, audio_alignment, assets, previous_manifest=None):
    manifest=build_manifest(scenes,audio_alignment,assets)
    changed=changed_scenes(manifest,previous_manifest or {"scenes":[]})
    return {
      "manifest":manifest,
      "render_scene_ids":changed,
      "skip_scene_ids":[s["scene_id"] for s in scenes if s["scene_id"] not in changed],
      "policy":"INCREMENTAL"
    }

def run_qa(scenes, rendered_outputs=None):
    rendered_outputs=rendered_outputs or {}
    reports=[]
    for s in scenes:
        report=qa_scene(s,rendered=rendered_outputs.get(s["scene_id"]))
        report["scene_id"]=s["scene_id"]
        report["repair_actions"]=repair_actions(report)
        reports.append(report)
    return {"scenes":reports,"course":course_qa(reports)}
