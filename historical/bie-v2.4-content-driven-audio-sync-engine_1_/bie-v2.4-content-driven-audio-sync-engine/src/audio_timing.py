def words(text):
    return [x for x in text.strip().split() if x]

def estimate_audio_duration_ms(text, wpm=145):
    return max(500, round(len(words(text))/wpm*60_000))

def build_audio_plan(scenes):
    total=0
    out=[]
    for s in scenes:
        duration=estimate_audio_duration_ms(s.get("narration",""))
        item={
            "scene_id":s["scene_id"],
            "audio":{
                "source":"TTS_OR_RECORDED",
                "estimated_duration_ms":duration,
                "sync_mode":"AUDIO_IS_AUTHORITATIVE",
                "word_timing_required":True
            }
        }
        out.append(item); total += duration
    return {"scenes":out,"estimated_total_duration_ms":total}
