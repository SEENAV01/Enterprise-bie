from validation import validate_derivation,validate_graph,validate_visual_semantics

def compile_scientific_visuals(equations=None,derivations=None,graphs=None,
                               visuals=None,vectors=None,fields=None):
    equations=equations or []; derivations=derivations or []
    graphs=graphs or []; visuals=visuals or []
    vectors=vectors or []; fields=fields or []
    checks=[]
    if derivations: checks.append(validate_derivation(derivations))
    checks += [validate_graph(g) for g in graphs]
    checks += [validate_visual_semantics(v) for v in visuals]
    errors=[e for c in checks for e in c["errors"]]
    return {
      "schema_version":"5.8",
      "equations":equations,"derivations":derivations,
      "graphs":graphs,"vectors":vectors,"fields":fields,
      "visual_semantics":visuals,
      "quality_gate":{"valid":not errors,"errors":errors}
    }
