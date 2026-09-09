SUPPORTED_VOICES = {"NEUTRAL","TEACHER","CONVERSATIONAL","NARRATOR"}

def voice(voice_id, profile, language="en", gender=None, age=None,
          pace=1.0, pitch=0.0):
    if profile not in SUPPORTED_VOICES:
        raise ValueError("UNSUPPORTED_VOICE_PROFILE")
    return {"voice_id":voice_id,"profile":profile,"language":language,
            "gender":gender,"age":age,"pace":pace,"pitch":pitch}

def valid(v):
    return bool(v["voice_id"] and v["profile"] in SUPPORTED_VOICES and v["language"])
