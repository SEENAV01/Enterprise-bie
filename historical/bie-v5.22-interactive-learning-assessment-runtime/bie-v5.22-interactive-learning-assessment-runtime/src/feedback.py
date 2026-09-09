def feedback(status,hint=None,explanation=None,next_action=None):
    return {"status":status,"hint":hint,"explanation":explanation,
            "next_action":next_action}

def choose_feedback(score,attempt):
    if score==1.0: return feedback("POSITIVE",next_action="CONTINUE")
    if attempt>=2: return feedback("TARGETED",next_action="SHOW_HINT_AND_RETRY")
    return feedback("PROMPT",next_action="RETRY")
