def dimensional_check(equation_terms):
    # equation_terms: [{"lhs": {...dimension...},"rhs":[...]}]
    errors=[]
    for eq in equation_terms:
        lhs=eq.get("lhs",{}).get("dimension",{}).get("exponents")
        for term in eq.get("rhs",[]):
            rhs=term.get("dimension",{}).get("exponents")
            if lhs!=rhs:
                errors.append({"type":"DIMENSION_MISMATCH",
                               "lhs":lhs,"rhs":rhs})
    return {"valid":not errors,"errors":errors}
