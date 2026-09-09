def select_delivery(policy,available=None):
    available=available or ["VIDEO","AUDIO","CAPTIONED_VIDEO","TEXT"]
    required=[]
    if policy.get("text_first"): required.append("TEXT")
    elif policy.get("audio_description"): required.append("CAPTIONED_VIDEO")
    elif policy.get("captions"): required.append("CAPTIONED_VIDEO")
    else: required.append("VIDEO")
    selected=[x for x in required if x in available]
    if not selected and "TEXT" in available: selected=["TEXT"]
    return {"selected":selected,"fallback_used":not bool([x for x in required if x in available])}
