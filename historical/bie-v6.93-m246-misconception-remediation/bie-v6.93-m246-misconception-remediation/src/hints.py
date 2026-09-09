def generate_hint(error_type,concept):
    hints={
      "DEFINITION_CONFUSION":f"Revisit the definition of {concept} and distinguish it from related terms.",
      "FORMULA_SELECTION":f"List the known quantities for {concept} before choosing a formula.",
      "UNIT_ERROR":"Check every quantity's unit before calculating.",
      "SIGN_DIRECTION":"Define the positive direction and inspect the sign convention.",
      "CAUSAL_REASONING":f"Trace the cause-and-effect chain for {concept} step by step.",
      "PREREQUISITE_GAP":f"Review the prerequisite concept needed for {concept}.",
      "CALCULATION":"Work through the calculation one operation at a time."
    }
    return hints.get(error_type,f"Review {concept} and try the problem again.")
