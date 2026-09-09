def state_machine(states,transitions,
                  initial_state):
    return {"states":states,
            "transitions":transitions,
            "initial_state":initial_state}

def can_transition(machine,current,event):
    return (current,event) in machine["transitions"]

def transition(machine,current,event):
    key=(current,event)
    if key not in machine["transitions"]:
        return {"status":"REJECTED","state":current}
    return {"status":"ACCEPTED",
            "state":machine["transitions"][key]}
