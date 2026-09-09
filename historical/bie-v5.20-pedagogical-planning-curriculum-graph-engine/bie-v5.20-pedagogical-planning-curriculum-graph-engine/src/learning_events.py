def learning_event(event_id,event_type,concept_id,
                   objective_ids=None,order=0):
    return {"event_id":event_id,"event_type":event_type,
            "concept_id":concept_id,"objective_ids":objective_ids or [],
            "order":order}

def valid_event_types():
    return ["MOTIVATE","EXPLAIN","VISUALIZE","EXAMPLE",
            "GUIDED_PRACTICE","INDEPENDENT_PRACTICE",
            "RETRIEVAL","ASSESS","REFLECT"]
