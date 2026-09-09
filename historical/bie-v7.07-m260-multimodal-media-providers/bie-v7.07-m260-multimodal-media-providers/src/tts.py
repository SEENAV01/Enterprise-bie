def create_tts_request(asset_id, text, language, voice=None):
    return {"asset_id":asset_id,"text":text,"language":language,
            "voice":voice,"status":"REQUESTED"}

def accept_tts(request, audio_uri, duration_seconds, sample_rate=48000):
    return {**request,"audio_uri":audio_uri,"duration_seconds":duration_seconds,
            "sample_rate":sample_rate,"status":"GENERATED"}
