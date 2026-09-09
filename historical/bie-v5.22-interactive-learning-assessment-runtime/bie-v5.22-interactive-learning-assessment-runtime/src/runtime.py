from evaluation import evaluate_response
from feedback import choose_feedback
from mastery import update_mastery
from hints import select_hint

def run_attempt(question,answer,learner_state):
    result=evaluate_response(question,answer)
    concept=question["concept_id"]
    old=learner_state.get("mastery",{}).get(concept,0.0)
    new=update_mastery(old,result.get("score"))
    learner_state.setdefault("mastery",{})[concept]=new
    fb=choose_feedback(result.get("score"),question.get("_attempt",1))
    hint=select_hint(question.get("hints",[]),question.get("_attempt",1))
    return {"evaluation":result,"feedback":fb,"hint":hint,
            "mastery":new,"learner_state":learner_state}
