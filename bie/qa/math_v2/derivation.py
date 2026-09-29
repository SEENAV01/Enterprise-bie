"""Reversible equation-chain checks; no inference from syntactic continuity alone."""
from .expression import Expr,num
from .algebra import Proof,compare_equations,equal_expressions,known_nonzero,interval,domain_issues
from .units import same_dimensions
from ..release_v2.contracts import ContractError

def check_step(step,scope):
    b,a=step.before,step.after;bounds,nz=scope.interval_bounds,scope.nonzero
    for e in (b.left,b.right,a.left,a.right,step.operand):
        issues=domain_issues(e,bounds,nz)
        if issues:return Proof('UNKNOWN',issues[0][0])
    try:
        if not same_dimensions(b.left,b.right,scope.symbol_units) or not same_dimensions(a.left,a.right,scope.symbol_units):return Proof('DISPROVED','DERIVATION_DIMENSION_MISMATCH')
        if step.rule=='rewrite':return compare_equations(b.left,b.right,a.left,a.right,bounds,nz)
        if step.rule=='swap':
            ok=equal_expressions(b.left,a.right) and equal_expressions(b.right,a.left)
        elif step.rule in ('add_both','subtract_both','multiply_both','divide_both'):
            op={'add_both':'add','subtract_both':'sub','multiply_both':'mul','divide_both':'div'}[step.rule]
            if op in ('mul','div') and not known_nonzero(step.operand,bounds,nz):return Proof('UNKNOWN','REVERSIBILITY_NONZERO_FACTOR_UNPROVEN')
            expected_left=Expr(op,'',(b.left,step.operand));expected_right=Expr(op,'',(b.right,step.operand))
            if not same_dimensions(expected_left,a.left,scope.symbol_units) or not same_dimensions(expected_right,a.right,scope.symbol_units):return Proof('DISPROVED','DERIVATION_OPERATION_DIMENSION_MISMATCH')
            ok=equal_expressions(a.left,expected_left) and equal_expressions(a.right,expected_right)
        elif step.rule=='square_both':
            lv,rv=interval(b.left,bounds),interval(b.right,bounds)
            if not ((lv.lo>=0 and rv.lo>=0) or (lv.hi<=0 and rv.hi<=0)):return Proof('UNKNOWN','SQUARING_BRANCH_NOT_PROVEN_INJECTIVE')
            ok=equal_expressions(a.left,Expr('pow','',(b.left,num(2)))) and equal_expressions(a.right,Expr('pow','',(b.right,num(2))))
        else:return Proof('UNKNOWN','UNSUPPORTED_DERIVATION_RULE')
        return Proof('PROVED','REVERSIBLE_STEP_CERTIFICATE') if ok else Proof('DISPROVED','STEP_OPERATION_MISMATCH')
    except ContractError as exc:return Proof('UNKNOWN',exc.code)
