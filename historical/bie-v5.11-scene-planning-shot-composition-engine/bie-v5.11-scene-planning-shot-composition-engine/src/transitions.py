TRANSITIONS=[
"CUT","FADE","DISSOLVE","MATCH_STATE","MORPH","WIPE","CONTINUE"
]

def transition(transition_id, kind, from_shot, to_shot,
               semantic_reason):
    if kind not in TRANSITIONS: raise ValueError("UNKNOWN_TRANSITION")
    return {
      "transition_id":transition_id,"kind":kind,
      "from_shot":from_shot,"to_shot":to_shot,
      "semantic_reason":semantic_reason
    }
