def pacing_profile(profile_id,attention_window=None,
                   density=None,recovery=None):
    return {"profile_id":profile_id,
            "attention_window":attention_window,
            "density":density,"recovery":recovery}

def pacing_constraint(segment_id,max_density=None,min_recovery=None,
                      transition_cost=None):
    return {"segment_id":segment_id,"max_density":max_density,
            "min_recovery":min_recovery,"transition_cost":transition_cost}
