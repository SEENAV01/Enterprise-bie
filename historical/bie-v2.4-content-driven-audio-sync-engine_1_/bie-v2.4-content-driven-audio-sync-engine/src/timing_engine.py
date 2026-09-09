def build_timeline(scenes, audio_plan):
    audio={x["scene_id"]:x["audio"] for x in audio_plan["scenes"]}
    cursor=0
    timeline=[]
    for s in scenes:
        a=audio[s["scene_id"]]
        # Placeholder timing until actual audio is available.
        duration=max(500,a["estimated_duration_ms"])
        timeline.append({
            "scene_id":s["scene_id"],
            "start_ms":cursor,
            "duration_ms":duration,
            "end_ms":cursor+duration,
            "sync_mode":"AUDIO_IS_AUTHORITATIVE"
        })
        cursor += duration
    return timeline

def retime_to_actual_audio(timeline, measured_audio_ms):
    out=[]
    cursor=0
    for item in timeline:
        d=measured_audio_ms[item["scene_id"]]
        out.append({**item,"start_ms":cursor,"duration_ms":d,"end_ms":cursor+d})
        cursor += d
    return out
