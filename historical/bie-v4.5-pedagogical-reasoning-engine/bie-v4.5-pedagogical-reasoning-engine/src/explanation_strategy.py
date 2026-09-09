def choose_mode(item):
    d=item.get("dimension")
    mapping={
      "DEFINITION":"EXPLAIN",
      "WHAT":"EXPLAIN",
      "WHY":"EXPLAIN_WITH_CAUSAL_MODEL",
      "HOW":"DEMONSTRATE_PROCESS",
      "PROCESS":"DEMONSTRATE_PROCESS",
      "DERIVATION":"DERIVE_STEP_BY_STEP",
      "FORMULA":"DERIVE_OR_VISUALIZE",
      "APPLICATION":"SHOW_APPLICATION",
      "EXAMPLE":"SHOW_EXAMPLE",
      "COMPARISON":"COMPARE",
      "EXCEPTION":"CONTRAST_AND_BOUNDARY",
      "COUNTEREXAMPLE":"COUNTEREXAMPLE",
      "WHEN":"CONTEXTUALIZE",
      "WHERE":"CONTEXTUALIZE",
      "WHO":"CONTEXTUALIZE"
    }
    return mapping.get(d,"EXPLAIN")

def build_strategy(items):
    return [{"item_id":i["id"],"mode":choose_mode(i)} for i in items]
