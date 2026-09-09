import json,sys
from pathlib import Path
from audio_timing import build_audio_plan
from timing_engine import build_timeline
from presentation_planner import plan_presentation
from sync_markers import make_markers

d=json.loads(Path(sys.argv[1]).read_text())
scenes=d["scene_dsl"]["scenes"]
audio=build_audio_plan(scenes)
timeline=build_timeline(scenes,audio)
presentation=[plan_presentation(s,a["audio"]["estimated_duration_ms"]) for s in scenes]
markers=[{"scene_id":s["scene_id"],"markers":make_markers(s["scene_id"],s.get("narration",""))} for s in scenes]
result={
 "schema_version":"2.4",
 "timing_policy":"CONTENT_DRIVEN_NO_FIXED_MAX_DURATION",
 "audio_policy":"AUDIO_IS_AUTHORITATIVE",
 "audio_plan":audio,
 "timeline":timeline,
 "presentation_plan":presentation,
 "sync_markers":markers
}
Path(sys.argv[2]).write_text(json.dumps(result,indent=2,ensure_ascii=False))
