from .contracts import *
def select_simulation_state_animation(ctx, *, simulation_id, model_fingerprint, seed, parameters, states, transitions, observed_execution=False):
    simulation_id=tok(simulation_id,"simulation_id");f=tok(model_fingerprint,"model_fingerprint").lower()
    if len(f)!=64 or any(c not in "0123456789abcdef" for c in f):raise AnimationSemanticError("model_fingerprint must be SHA-256")
    if isinstance(seed,bool) or not isinstance(seed,int):raise AnimationSemanticError("seed must be integer")
    states=tuple(states);transitions=tuple(transitions)
    if len(states)<2:raise AnimationSemanticError("at least two states required")
    state_ids=[tok(x["state_id"],"state_id") for x in states]
    if len(set(state_ids))!=len(state_ids):raise AnimationSemanticError("duplicate state id")
    valid=set(state_ids)
    for tr in transitions:
        if tr.get("from") not in valid or tr.get("to") not in valid or not tr.get("transition_id"):raise AnimationSemanticError("invalid transition")
    span=ctx.cue.end_ms-ctx.cue.start_ms;steps=[]
    for i,tr in enumerate(transitions):
        s=ctx.cue.start_ms+span*i//max(1,len(transitions));e=ctx.cue.start_ms+span*(i+1)//max(1,len(transitions))
        steps.append(AnimationStep(f"{ctx.intent_id}:sim:{i}","simulation_state",(simulation_id,),s,max(s+1,e),
                                   "declared_simulation_state_transition",tr["from"],tr["to"],{"transition_id":tr["transition_id"]}))
    status="PASS" if observed_execution else "REVIEW"
    return make_decision(ctx,":simulation","simulation_state",status,.92 if observed_execution else .62,steps,
                         ("observed_execution_available",) if observed_execution else ("declared_states_are_not_execution_evidence",),
                         {"simulation_id":simulation_id,"model_fingerprint":f,"seed":seed,"parameters":canonical(dict(parameters)),
                          "state_ids":state_ids,"observed_execution":observed_execution})
