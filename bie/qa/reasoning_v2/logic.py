"""Bounded propositional checks. Formal entailment is NOT premise truth.

No eval(), language parsing, arithmetic theorem proving or causal discovery.
An inconsistent premise set is rejected rather than vacuously certified.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from ..release_v2.contracts import ContractError, choice, token, integer

@dataclass(frozen=True, slots=True)
class Expr:
    op: str
    atom: str = ''
    args: tuple[Expr, ...] = ()

    def __post_init__(self):
        choice(self.op, ('atom','not','and','or','implies','iff'), 'expr.op')
        if type(self.args) is not tuple or any(type(a) is not Expr for a in self.args):
            raise ContractError('INVALID_EXPRESSION_ARGS')
        if self.op == 'atom':
            token(self.atom, 'expr.atom')
            if self.args: raise ContractError('ATOM_HAS_ARGS')
        else:
            if type(self.atom) is not str or self.atom != '': raise ContractError('OPERATOR_HAS_ATOM')
            expected = 1 if self.op == 'not' else 2
            if len(self.args) != expected: raise ContractError('EXPRESSION_ARITY')
        stack=[(self,1)]; count=0
        while stack:
            node,depth=stack.pop(); count+=1
            if count>127 or depth>16: raise ContractError('EXPRESSION_RESOURCE_LIMIT')
            stack.extend((a,depth+1) for a in node.args)

    @property
    def atoms(self) -> tuple[str,...]:
        out=set(); stack=[self]
        while stack:
            n=stack.pop()
            if n.op=='atom': out.add(n.atom)
            stack.extend(n.args)
        return tuple(sorted(out))

    @property
    def node_count(self) -> int:
        return 1+sum(x.node_count for x in self.args)


def truth(expr: Expr, assignment: dict[str,bool]) -> bool:
    if type(expr) is not Expr or type(assignment) is not dict: raise ContractError('INVALID_TRUTH_INPUT')
    if any(type(v) is not bool for v in assignment.values()): raise ContractError('NONBOOLEAN_ASSIGNMENT')
    if not set(expr.atoms) <= set(assignment): raise ContractError('INCOMPLETE_ASSIGNMENT')
    def run(x):
        if x.op=='atom': return assignment[x.atom]
        if x.op=='not': return not run(x.args[0])
        a,b=run(x.args[0]),run(x.args[1])
        if x.op=='and': return a and b
        if x.op=='or': return a or b
        if x.op=='implies': return (not a) or b
        return a==b
    return run(expr)

@dataclass(frozen=True, slots=True)
class ProofCheck:
    status: str
    assignments_required: int
    assignments_checked: int
    satisfying_premise_assignments: int
    witness: tuple[tuple[str,bool], ...]


def entailment(premises: tuple[Expr,...], conclusion: Expr, *, max_atoms: int=12,
               max_assignments: int=4096, max_node_visits: int=2000000) -> ProofCheck:
    if type(premises) is not tuple or not 1<=len(premises)<=64 or any(type(p) is not Expr for p in premises):
        raise ContractError('INVALID_PROOF_PREMISES')
    if type(conclusion) is not Expr: raise ContractError('INVALID_PROOF_CONCLUSION')
    integer(max_atoms,'max_atoms',1,12); integer(max_assignments,'max_assignments',1,1048576)
    integer(max_node_visits,'max_node_visits',1,20000000)
    atoms=tuple(sorted({a for p in premises+(conclusion,) for a in p.atoms}))
    # Do not compute an unbounded integer shift on hostile expressions.
    if len(atoms)>max_atoms: return ProofCheck('RESOURCE_LIMIT',0,0,0,())
    required=1<<len(atoms)
    if required>max_assignments or required*sum(p.node_count for p in premises+(conclusion,))>max_node_visits:
        return ProofCheck('RESOURCE_LIMIT',required,0,0,())
    checked=0; satisfied=0
    for row in product((False,True),repeat=len(atoms)):
        assignment=dict(zip(atoms,row));checked+=1
        if all(truth(p,assignment) for p in premises):
            satisfied+=1
            if not truth(conclusion,assignment):
                return ProofCheck('COUNTEREXAMPLE',required,checked,satisfied,tuple(zip(atoms,row)))
    if not satisfied: return ProofCheck('INCONSISTENT_PREMISES',required,checked,0,())
    return ProofCheck('ENTAILED',required,checked,satisfied,())
