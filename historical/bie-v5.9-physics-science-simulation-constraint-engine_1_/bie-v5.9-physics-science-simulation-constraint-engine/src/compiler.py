from validation import validate_law,validate_simulation
from dimensional import dimensional_check
from constraints import check_constraints

def compile_simulation(laws=None,simulations=None,
                       constraints=None,dimension_checks=None,states=None):
    laws=laws or []; simulations=simulations or []
    constraints=constraints or []; dimension_checks=dimension_checks or []
    checks=[validate_law(x) for x in laws]+[validate_simulation(x) for x in simulations]
    dim=dimensional_check(dimension_checks) if dimension_checks else {"valid":True,"errors":[]}
    constraint_status=check_constraints(states or {},constraints)
    errors=[e for c in checks for e in c["errors"]]+dim["errors"]
    return {
      "schema_version":"5.9",
      "laws":laws,"simulations":simulations,
      "constraints":constraints,
      "constraint_status":constraint_status,
      "dimension_check":dim,
      "quality_gate":{"valid":not errors,"errors":errors}
    }
