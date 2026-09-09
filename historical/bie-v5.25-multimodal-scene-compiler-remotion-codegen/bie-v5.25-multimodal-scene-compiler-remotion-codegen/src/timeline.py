def timeline(scene_id,duration_seconds,fps=30,
            audio_ref=None,cues=None):
    return {"scene_id":scene_id,"duration_seconds":duration_seconds,
            "fps":fps,"audio_ref":audio_ref,"cues":cues or []}
