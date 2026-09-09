def evaluation_rule(rule_id,response_type,method,
                    expected=None,tolerance=None):
    return {"rule_id":rule_id,"response_type":response_type,
            "method":method,"expected":expected,
            "tolerance":tolerance}

def evaluate_response(rule,response):
    method=rule.get("method")
    expected=rule.get("expected")
    if method=="EXACT":
        return {"correct":response==expected,"score":1 if response==expected else 0}
    if method=="NUMERICAL_TOLERANCE":
        try:
            ok=abs(float(response)-float(expected))<=float(rule.get("tolerance",0))
            return {"correct":ok,"score":1 if ok else 0}
        except Exception:
            return {"correct":False,"score":0}
    return {"correct":None,"score":None,"needs_human_or_model_eval":True}
