def equation(equation_id, latex, variables=None, meaning=None):
    return {
      "equation_id":equation_id,"latex":latex,
      "variables":variables or [],"meaning":meaning or {}
    }

def derivation_step(step_id, expression, operation, from_step=None,
                    explanation=""):
    return {
      "step_id":step_id,"expression":expression,
      "operation":operation,"from_step":from_step,
      "explanation":explanation
    }
