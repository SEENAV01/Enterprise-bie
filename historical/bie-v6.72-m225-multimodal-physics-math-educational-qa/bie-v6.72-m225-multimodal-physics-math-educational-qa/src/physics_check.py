def check_physics_relation(observed,expected,tolerance=0.05,units_match=True):
    error=abs(observed-expected)
    return {"passed":error<=tolerance and units_match,"error":error,
            "tolerance":tolerance,"units_match":units_match}
def check_units(actual,expected):
    return {"passed":actual==expected,"actual":actual,"expected":expected}
