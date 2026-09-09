from collections import Counter

def coverage_report(extractions):
    counts=Counter(x["dimension"] for x in extractions)
    return {
      "dimension_counts":dict(counts),
      "dimensions_found":sorted(counts),
      "empty_dimensions":[
        d for d in [
          "WHAT","WHY","HOW","WHEN","WHERE","WHO","DEFINITION","PROCESS",
          "CAUSE","DERIVATION","EXAMPLE","APPLICATION","ASSUMPTION",
          "EXCEPTION","EVIDENCE","PREREQUISITE","DEPENDENCY"
        ] if d not in counts
      ]
    }
