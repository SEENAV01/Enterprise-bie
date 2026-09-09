from learner import learner,validate_learner
from skill_state import skill_state,update_skill
from skill_tracing import trace_batch
from knowledge_state import knowledge_state,persist_state,load_state
from selection import select_lessons

def build_learner_runtime():
    L=learner("learner-001",{"mode":"personalized"})
    store={}
    states={"charge":skill_state("charge",0.9,3),
            "field":skill_state("field",0.55,2),
            "force":skill_state("force",0.35,2)}
    responses=[
      {"item_id":"a1","score":0.5,"skill_ids":["field"]},
      {"item_id":"a2","score":0.4,"skill_ids":["force"]}]
    traces=trace_batch(responses)
    states["field"]=update_skill(states["field"],0.5)
    states["force"]=update_skill(states["force"],0.4)
    ks=knowledge_state(L["learner_id"],{k:v["mastery"] for k,v in states.items()})
    persistence=persist_state(ks,store)
    loaded=load_state(L["learner_id"],store)
    lessons=[
      {"lesson_id":"field-review","skill_ids":["field"]},
      {"lesson_id":"force-reteach","skill_ids":["force","field"]},
      {"lesson_id":"charge-advanced","skill_ids":["charge"]}]
    selected=select_lessons(lessons,loaded["skills"],2)
    return {"schema_version":"6.79","learner":L,"skill_states":states,
            "skill_traces":traces,"knowledge_state":ks,
            "persistence":persistence,"loaded_state":loaded,
            "personalized_selection":selected,
            "learner_model_gate":{"valid":validate_learner(L) and
                persistence["persisted"] and len(selected)==2,"errors":[]}}
