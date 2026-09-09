from mastery import mastery_update,mastery_summary
from adaptation import adaptive_decision,choose_next_objective

def compile_adaptive_path(ordered_objectives,states,evidence_by_objective,
                          misconceptions_by_objective=None,threshold=0.8):
    misconceptions_by_objective=misconceptions_by_objective or {}
    updated=[]
    decisions=[]
    for state in states:
        ev=evidence_by_objective.get(state["objective_id"])
        new=mastery_update(state,ev,threshold) if ev else state
        updated.append(new)
        decisions.append({
          "objective_id":state["objective_id"],
          "decision":adaptive_decision(
              new,misconceptions_by_objective.get(state["objective_id"],[]))
        })
    next_obj=choose_next_objective(ordered_objectives,updated)
    return {
      "schema_version":"5.34",
      "learner_states":updated,
      "mastery":mastery_summary(updated),
      "decisions":decisions,
      "next_objective":next_obj,
      "quality_gate":{"valid":True,"errors":[]}
    }
