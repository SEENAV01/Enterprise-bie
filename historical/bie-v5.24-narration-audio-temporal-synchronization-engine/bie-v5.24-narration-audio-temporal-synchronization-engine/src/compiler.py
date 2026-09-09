from sync import scene_duration,align_cues
from timeline import temporal_timeline
from captions import captions_from_phrases

def compile_temporal_scene(scene_id,audio_duration,phrases,cues,
                           audio_ref=None):
    duration=scene_duration(audio_duration)
    caps=captions_from_phrases(phrases)
    aligned=align_cues(phrases,cues)
    timeline=temporal_timeline(scene_id,duration,audio_ref,
                               [c["caption_id"] for c in caps],
                               [c["cue_id"] for c in aligned])
    errors=[]
    for p in phrases:
        if p["end"]>duration: errors.append("PHRASE_EXCEEDS_SCENE")
    return {"schema_version":"5.24","timeline":timeline,
            "captions":caps,"visual_cues":aligned,
            "quality_gate":{"valid":not errors,"errors":errors}}
