def choose_difficulty(mastery,history=None):
    history=history or {}
    if mastery>=0.85: level="ADVANCED"
    elif mastery>=0.65: level="INTERMEDIATE"
    else: level="FOUNDATION"
    if history.get("recent_failures",0)>=2 and level!="FOUNDATION":
        level="FOUNDATION"
    return {"level":level,"mastery":mastery}

def adapt_unit(unit,difficulty):
    return {**unit,"difficulty":difficulty["level"],
            "adaptation":{"scaffold":difficulty["level"]=="FOUNDATION",
                          "challenge":difficulty["level"]=="ADVANCED"}}
