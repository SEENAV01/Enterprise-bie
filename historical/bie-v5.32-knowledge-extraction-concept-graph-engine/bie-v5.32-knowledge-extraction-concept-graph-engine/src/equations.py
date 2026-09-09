def equation(equation_id,formula,variables=None,units=None,
             source_refs=None):
    return {"equation_id":equation_id,"formula":formula,
            "variables":variables or [],"units":units or [],
            "source_refs":source_refs or []}
