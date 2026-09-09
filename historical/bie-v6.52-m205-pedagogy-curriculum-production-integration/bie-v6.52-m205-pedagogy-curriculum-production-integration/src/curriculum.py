def unit(unit_id, title, objective_ids=None, prerequisite_unit_ids=None,
         lesson_ids=None, metadata=None):
    return {"unit_id": unit_id, "title": title,
            "objective_ids": objective_ids or [],
            "prerequisite_unit_ids": prerequisite_unit_ids or [],
            "lesson_ids": lesson_ids or [],
            "metadata": metadata or {}}

def ordered(units):
    return units

def valid(unit_item):
    return bool(unit_item["unit_id"] and unit_item["title"])
