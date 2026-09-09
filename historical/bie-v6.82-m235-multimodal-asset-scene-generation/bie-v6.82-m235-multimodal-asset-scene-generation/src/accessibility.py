def scene_accessibility(profile,assets):
    required=[]
    if profile.get("captions"): required.append("CAPTIONS")
    if profile.get("audio_description"): required.append("AUDIO_DESCRIPTION")
    if profile.get("high_contrast"): required.append("HIGH_CONTRAST")
    if profile.get("reduced_motion"): required.append("REDUCED_MOTION")
    return {"required":required,
            "asset_count":len(assets),
            "compliant":all(a.get("accessibility",{}).get(r.lower(),True)
                            for a in assets for r in [] )} 
