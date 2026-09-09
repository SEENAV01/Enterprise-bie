def visual_state(state_id,values=None,time_hint=None):
    return {"state_id":state_id,"values":values or {},
            "time_hint":time_hint}

def transition(transition_id,from_state,to_state,behavior,
               duration_hint=None,easing=None):
    return {"transition_id":transition_id,"from_state":from_state,
            "to_state":to_state,"behavior":behavior,
            "duration_hint":duration_hint,"easing":easing}
