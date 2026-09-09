OBJECTIVE_TYPES=[
"UNDERSTAND","EXPLAIN","DERIVE","SOLVE","APPLY","COMPARE",
"RECALL","TRANSFER","CREATE"
]

def normalize_objective(obj):
    return {
      "type":obj.get("type","UNDERSTAND"),
      "topic":obj["topic"],
      "depth":obj.get("depth","CORE"),
      "constraints":obj.get("constraints",{})
    }
