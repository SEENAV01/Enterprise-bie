def select_voice(preferences,available=None):
    available=available or ["neutral","warm","clear"]
    requested=preferences.get("voice","clear")
    selected=requested if requested in available else ("clear" if "clear" in available else available[0])
    return {"requested":requested,"selected":selected,
            "language":preferences.get("language","en"),
            "pace":preferences.get("pace","adaptive")}

def narration_spec(voice,accessibility):
    return {"voice":voice["selected"],"language":voice["language"],
            "pace":voice["pace"],
            "audio_description":bool(accessibility.get("audio_description"))}
