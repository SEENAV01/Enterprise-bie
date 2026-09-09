def visual_constraints(policy):
    return {"density":policy.get("visual_density","balanced"),
            "high_contrast":bool(policy.get("high_contrast")),
            "reduced_motion":bool(policy.get("reduced_motion"))}

def narration_constraints(policy):
    return {"language":policy.get("language","en"),
            "pace":policy.get("pace","adaptive"),
            "audio_description":bool(policy.get("audio_description"))}
