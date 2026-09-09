def composition(composition_id,inputs,
                timeline=None,settings=None):
    return {"composition_id":composition_id,
            "inputs":inputs,"timeline":timeline or [],
            "settings":settings or {}}

def composition_input(asset_ref,role,start=None,
                      duration=None):
    return {"asset":asset_ref,"role":role,
            "start":start,"duration":duration}
