def quorum_state(nodes,available):
    return {"nodes":nodes,"available":available,
            "quorum":available > nodes/2}

def safe_for_write(state):
    return bool(state.get("quorum"))

def stale_owner(owner_token,current_token):
    return owner_token < current_token
