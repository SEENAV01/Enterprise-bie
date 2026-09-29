"""Pinned native MATH contract adapters. Legacy PASS never becomes QA acceptance."""
from dataclasses import dataclass,asdict
import math
from ...math_intelligence.expression_ast import Node
from ...math_intelligence.equation_ast import Equation as NativeEquation
from ...math_intelligence.dimensional_analysis import Dimension,combine,dimension_of
from ...math_intelligence.derivation_chain import Step,validate_chain
from ...math_intelligence.numerical_qa import NumericalQA,assess_numeric
from ..release_v2.contracts import ContractError,digest
from .expression import Expr,parse,num,SYM,rational
from .models import Equation

def _import_node(node:Node,depth=0):
    if depth>24 or type(node) is not Node or type(node.children) is not tuple:raise ContractError('INVALID_NATIVE_MATH_NODE')
    if type(node.value) is not str or len(node.value)>160:raise ContractError('INVALID_NATIVE_MATH_VALUE')
    if node.kind=='atom' and not node.children:
        try:return num(node.value)
        except ContractError:
            if SYM.fullmatch(node.value):return Expr('sym',node.value)
            raise ContractError('NATIVE_ATOM_IS_NOT_ONE_TOKEN')
    if node.kind=='binary' and node.value in ('+','-','*','/','^') and len(node.children)==2:
        return Expr({'+':'add','-':'sub','*':'mul','/':'div','^':'pow'}[node.value],'',tuple(_import_node(x,depth+1) for x in node.children))
    raise ContractError('UNSUPPORTED_NATIVE_MATH_NODE')

def import_node(node:Node,original_text:str):
    imported=_import_node(node)
    original=parse(original_text)
    if imported!=original:raise ContractError('NATIVE_SOURCE_PARSE_MISMATCH')
    return imported

def import_equation(native:NativeEquation):
    if type(native) is not NativeEquation or native.relation!='=':raise ContractError('UNSUPPORTED_NATIVE_EQUATION_RELATION')
    return Equation(parse(native.left),parse(native.right))

def export_dimension(values):
    if type(values) is not tuple or len(values)!=7 or any(type(v) is not int or abs(v)>32 for v in values):raise ContractError('INVALID_NATIVE_DIMENSION')
    native=Dimension(*values)
    # Exercise the actual native dimension algebra, not a renamed local copy.
    expected=dimension_of([(u,p) for u,p in zip(('m','kg','s','A','K','mol','cd'),values) if p])
    if combine(Dimension(),native)!=expected:raise ContractError('NATIVE_DIMENSION_DIVERGENCE')
    return native

def inspect_native_chain(steps):
    if type(steps) is not tuple or not 1<=len(steps)<=64 or any(type(s) is not Step for s in steps):raise ContractError('INVALID_NATIVE_CHAIN')
    for s in steps:
        if type(s.before) is not str or type(s.after) is not str or max(len(s.before),len(s.after))>2048:raise ContractError('INVALID_NATIVE_CHAIN_TEXT')
    r=validate_chain(list(steps))
    return dict(native=asdict(r),payload_digest=digest([asdict(s) for s in steps]),mathematical_proof_available=False,product_accepted=False)

def inspect_native_numeric(expected,actual,tolerance):
    for x in (expected,actual,tolerance):
        if type(x) not in (int,float) or not math.isfinite(x):raise ContractError('NONFINITE_NATIVE_NUMERIC')
    if tolerance<0:raise ContractError('NEGATIVE_NATIVE_TOLERANCE')
    r=assess_numeric(expected,actual,tolerance,finite_required=True)
    return dict(native=dict(passed=r.passed,error_repr=repr(r.error),failures=r.failures),exact_recomputation_available=False,product_accepted=False)
