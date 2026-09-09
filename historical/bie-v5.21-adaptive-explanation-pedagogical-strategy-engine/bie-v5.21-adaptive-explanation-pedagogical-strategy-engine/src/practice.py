def practice_plan(concept_id,density="ADAPTIVE",
                  guided_items=2,independent_items=3,
                  retrieval=True):
    return {"concept_id":concept_id,"density":density,
            "guided_items":guided_items,
            "independent_items":independent_items,
            "retrieval":retrieval}
