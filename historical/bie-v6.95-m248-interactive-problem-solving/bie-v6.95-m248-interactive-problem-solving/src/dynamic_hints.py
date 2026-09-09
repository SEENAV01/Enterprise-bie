LEVELS=["CONCEPT","STRATEGY","STEP","PARTIAL","FULL"]

def next_hint_level(current, validation):
    if validation.get("valid"): return "WITHDRAW"
    i=LEVELS.index(current)
    return LEVELS[min(i+1,len(LEVELS)-1)]

def dynamic_hint(level, step_text):
    if level=="CONCEPT": return "Recall the governing concept before calculating."
    if level=="STRATEGY": return "Identify the relationship that connects the known values to the target."
    if level=="STEP": return f"Focus on this step: {step_text}"
    if level=="PARTIAL": return f"Start from: {step_text}"
    return f"Full solution guidance: {step_text}"
