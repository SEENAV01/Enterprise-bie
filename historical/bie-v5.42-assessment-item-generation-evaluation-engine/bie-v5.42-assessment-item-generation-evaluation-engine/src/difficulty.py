def difficulty_profile(level=None,intrinsic=None,
                       reasoning_depth=None,novelty=None):
    return {"level":level,"intrinsic":intrinsic,
            "reasoning_depth":reasoning_depth,"novelty":novelty}

def difficulty_score(profile):
    vals=[v for v in [profile.get("intrinsic"),
                      profile.get("reasoning_depth"),
                      profile.get("novelty")] if isinstance(v,(int,float))]
    return sum(vals)/len(vals) if vals else profile.get("level")
