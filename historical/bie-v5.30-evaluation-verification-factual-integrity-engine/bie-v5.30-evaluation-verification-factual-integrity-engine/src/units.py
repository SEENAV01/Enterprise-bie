def unit_check(value,unit,expected_unit):
    return {"valid":unit==expected_unit,"value":value,
            "unit":unit,"expected_unit":expected_unit}

def dimensional_check(dimensions,expected_dimensions):
    return {"valid":dimensions==expected_dimensions,
            "dimensions":dimensions,
            "expected_dimensions":expected_dimensions}
