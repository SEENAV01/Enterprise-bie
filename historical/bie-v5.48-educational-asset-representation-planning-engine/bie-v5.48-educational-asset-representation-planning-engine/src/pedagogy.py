def pedagogical_intent(intent_id,purpose,learner_need=None,
                     evidence_goal=None,complexity=None):
    return {"intent_id":intent_id,"purpose":purpose,
            "learner_need":learner_need,
            "evidence_goal":evidence_goal,
            "complexity":complexity}

def intents():
    return ["INTRODUCE","EXPLAIN","COMPARE","VISUALIZE",
            "PRACTICE","PREDICT","SIMULATE","RECALL",
            "DIAGNOSE","ASSESS","REINFORCE","TRANSFER"]
