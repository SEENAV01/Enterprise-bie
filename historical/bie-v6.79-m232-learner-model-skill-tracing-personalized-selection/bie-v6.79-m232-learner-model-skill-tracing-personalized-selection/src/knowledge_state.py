def knowledge_state(learner_id,skills=None,version=1):
    return {"learner_id":learner_id,"version":version,"skills":skills or {}}

def persist_state(state,store):
    store[state["learner_id"]]=state
    return {"persisted":True,"learner_id":state["learner_id"],"version":state["version"]}

def load_state(learner_id,store):
    return store.get(learner_id)
