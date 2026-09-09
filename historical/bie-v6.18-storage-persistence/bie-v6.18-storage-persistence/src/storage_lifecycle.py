def lifecycle(entity_name,
             states=None):
    return {"entity":entity_name,
            "states":states or
            ["ACTIVE","ARCHIVED","DELETED"]}

def valid_transition(current,next_state):
    allowed={
      "ACTIVE":{"ARCHIVED","DELETED"},
      "ARCHIVED":{"ACTIVE","DELETED"},
      "DELETED":set()
    }
    return next_state in allowed.get(current,set())
