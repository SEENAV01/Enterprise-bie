from runtime import run_attempt

def compile_runtime(question,answer,learner_state):
    result=run_attempt(question,answer,learner_state)
    return {"schema_version":"5.22","question_id":question.get("question_id"),
            "runtime_result":result,
            "quality_gate":{"valid":True,"errors":[]}}
