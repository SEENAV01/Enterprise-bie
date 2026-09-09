def learner_state(learner_id,mastery=None,attempt_history=None,
                  misconceptions=None):
    return {"learner_id":learner_id,"mastery":mastery or {},
            "attempt_history":attempt_history or [],
            "misconceptions":misconceptions or []}

def record_attempt(state,attempt):
    state["attempt_history"].append(attempt)
    return state
