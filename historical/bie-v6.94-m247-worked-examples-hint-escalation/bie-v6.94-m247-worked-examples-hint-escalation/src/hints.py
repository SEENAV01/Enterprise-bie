LEVELS=["CONCEPT","STRATEGY","STEP","PARTIAL_SOLUTION","FULL_SOLUTION"]

def hint_for(example,level,index=0):
    steps=example.get("steps",[])
    if level=="CONCEPT":
        return "Recall the governing concept and identify what the question asks."
    if level=="STRATEGY":
        return "Choose the principle or equation that connects the known quantities to the target."
    if level=="STEP":
        return steps[index] if index<len(steps) else "Check the next algebraic or reasoning step."
    if level=="PARTIAL_SOLUTION":
        return "Start with the first required substitution or reasoning step, then continue."
    return f"Full worked solution: {example.get('final_answer')}"

def escalate_hint(level,correct=False):
    if correct:return "WITHDRAW"
    i=LEVELS.index(level)
    return LEVELS[min(i+1,len(LEVELS)-1)]
