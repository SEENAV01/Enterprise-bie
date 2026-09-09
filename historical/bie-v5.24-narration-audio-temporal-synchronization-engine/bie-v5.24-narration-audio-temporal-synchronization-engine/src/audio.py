def audio_asset(audio_id,path,voice_id=None,
               sample_rate=None,duration_seconds=None,language="en"):
    return {"audio_id":audio_id,"path":path,"voice_id":voice_id,
            "sample_rate":sample_rate,"duration_seconds":duration_seconds,
            "language":language}
