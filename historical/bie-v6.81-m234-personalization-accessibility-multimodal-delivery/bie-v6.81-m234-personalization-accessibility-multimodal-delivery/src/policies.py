def personalization_policy(preferences,accessibility):
    policy={"pace":preferences.get("pace","adaptive"),
            "visual_density":preferences.get("visual_density","balanced"),
            "language":preferences.get("language","en")}
    if preferences.get("caption_required"): policy["captions"]=True
    if accessibility.get("captions"): policy["captions"]=True
    if accessibility.get("audio_description"): policy["audio_description"]=True
    if accessibility.get("high_contrast"): policy["high_contrast"]=True
    if accessibility.get("reduced_motion"): policy["reduced_motion"]=True
    if accessibility.get("text_first"): policy["text_first"]=True
    return policy
