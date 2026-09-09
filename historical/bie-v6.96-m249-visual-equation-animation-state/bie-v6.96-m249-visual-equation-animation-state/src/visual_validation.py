def validate_visual_step(expected_state,actual_state):
    expected={k:v for k,v in expected_state.items() if k!="transient"}
    actual={k:v for k,v in actual_state.items() if k!="transient"}
    return {"valid":expected==actual,
            "missing":[k for k in expected if k not in actual],
            "mismatched":[k for k in expected if k in actual and expected[k]!=actual[k]]}

def validate_relation(diagram,source,target,relation):
    return any(r.get("source")==source and r.get("target")==target and
               r.get("relation")==relation for r in diagram.get("relations",[]))
