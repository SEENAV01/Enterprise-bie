from timeline import timeline,add_track,update_duration
from adaptive_timing import sync_check

def compile_long_form_timeline(narration,visual_beats,captions,
                               audio_clips=None,music=None,fps=30):
    tl=timeline("lesson_timeline",fps)
    add_track(tl,"narration","NARRATION",narration)
    add_track(tl,"visual_beats","VISUAL_BEATS",visual_beats)
    add_track(tl,"captions","CAPTIONS",captions)
    add_track(tl,"audio","AUDIO",audio_clips or [])
    if music: add_track(tl,"music","MUSIC",music)
    update_duration(tl)
    q=sync_check(narration,visual_beats,captions)
    return {"schema_version":"5.14","timeline":tl,
            "synchronization":q,
            "quality_gate":{"valid":q["valid"],"errors":q["errors"]}}
