def learner(learner_id,metadata=None):
    return {"learner_id":learner_id,"metadata":metadata or {}}

def validate_learner(l):
    return bool(l.get("learner_id"))
