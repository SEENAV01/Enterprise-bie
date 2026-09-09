def constraint(constraint_id,expression,kind="HARD",
               description=""):
    if kind not in ("HARD","SOFT"): raise ValueError("UNKNOWN_CONSTRAINT_KIND")
    return {
      "constraint_id":constraint_id,"expression":expression,
      "kind":kind,"description":description
    }

def check_constraints(state,constraints):
    # Production backend evaluates expressions with a trusted math engine.
    # This layer records the contract and returns unresolved checks explicitly.
    return [
      {"constraint_id":c["constraint_id"],"status":"PENDING_EVALUATION",
       "kind":c["kind"]} for c in constraints
    ]
