def animation_instruction(target,property_name,from_value,to_value,
                          start,end,easing="linear"):
    return {"target":target,"property":property_name,
            "from":from_value,"to":to_value,"start":start,"end":end,
            "easing":easing}

def animation_graph(instructions):
    return {"instructions":instructions}
