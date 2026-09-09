def learner(learner_id,profile=None):
    return {"learner_id":learner_id,"profile":profile or {}}

def mastery_state(objective_id,status="UNKNOWN",score=None,attempts=0):
    return {"objective_id":objective_id,"status":status,
            "score":score,"attempts":attempts}
