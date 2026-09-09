def quality_profile(complexity,accuracy="HIGH",visual="HIGH",
                   pedagogy="HIGH"):
    return {"complexity":complexity,"accuracy":accuracy,
            "visual":visual,"pedagogy":pedagogy}

def quality_score(profile):
    levels={"LOW":1,"MEDIUM":2,"HIGH":3,"EXTREME":4}
    return sum(levels.get(profile.get(k,"MEDIUM"),2)
               for k in ("accuracy","visual","pedagogy"))
