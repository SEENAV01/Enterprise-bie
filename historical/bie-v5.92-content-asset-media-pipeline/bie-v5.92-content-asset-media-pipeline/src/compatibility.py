def compatibility_rule(input_kind,output_format,
                       supported=True,reason=None):
    return {"input_kind":input_kind,
            "output_format":output_format,
            "supported":supported,"reason":reason}

def compatible(rule):
    return bool(rule.get("supported"))
