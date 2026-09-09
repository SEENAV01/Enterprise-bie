def accessibility_profile(captions=False,audio_description=False,
                          high_contrast=False,reduced_motion=False,
                          text_first=False):
    return {"captions":captions,"audio_description":audio_description,
            "high_contrast":high_contrast,"reduced_motion":reduced_motion,
            "text_first":text_first}

def accessibility_requirements(profile):
    req=[]
    if profile.get("captions"): req.append("CAPTIONS")
    if profile.get("audio_description"): req.append("AUDIO_DESCRIPTION")
    if profile.get("high_contrast"): req.append("HIGH_CONTRAST")
    if profile.get("reduced_motion"): req.append("REDUCED_MOTION")
    if profile.get("text_first"): req.append("TEXT_FIRST")
    return req
