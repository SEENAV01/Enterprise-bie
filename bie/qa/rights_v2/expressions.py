"""Bounded license-selection syntax; no built-in interpretation of license terms.

AND requires both branches; OR requires an explicit branch selection; WITH is one
indivisible license-plus-exception atom. Standard-looking names are not certified
against an SPDX catalog. '+' and external DocumentRef references require review.
No expression, including a recognized name, creates permission by itself.
"""
import re
from ..release_v2.contracts import ContractError

_TOKEN = re.compile(r'[A-Za-z0-9][A-Za-z0-9.-]*|\(|\)')

def parse(expression: str):
    if type(expression) is not str or not expression or len(expression)>2048:
        raise ContractError('RIGHTS_EXPRESSION_SIZE')
    tokens=[];pos=0
    while pos<len(expression):
        if expression[pos]==' ':pos+=1;continue
        m=_TOKEN.match(expression,pos)
        if not m:raise ContractError('RIGHTS_EXPRESSION_UNSUPPORTED')
        tokens.append(m.group());pos=m.end()
    if len(tokens)>128:raise ContractError('RIGHTS_EXPRESSION_BUDGET')
    cursor=0
    def atom(depth):
        nonlocal cursor
        if depth>16:raise ContractError('RIGHTS_EXPRESSION_DEPTH')
        if cursor>=len(tokens):raise ContractError('RIGHTS_EXPRESSION_SYNTAX')
        t=tokens[cursor];cursor+=1
        if t=='(':
            n=disjunction(depth+1)
            if cursor>=len(tokens) or tokens[cursor]!=')':raise ContractError('RIGHTS_EXPRESSION_SYNTAX')
            cursor+=1;return n
        if t in ('AND','OR','WITH',')') or t.lower() in ('and','or','with','none','noassertion'):
            raise ContractError('RIGHTS_EXPRESSION_UNKNOWN')
        name=t.lower()
        if cursor<len(tokens) and tokens[cursor]=='WITH':
            cursor+=1
            if cursor>=len(tokens) or tokens[cursor] in ('AND','OR','WITH','(',')'):
                raise ContractError('RIGHTS_EXPRESSION_SYNTAX')
            exception=tokens[cursor]
            if exception.lower() in ('and','or','with','none','noassertion'):
                raise ContractError('RIGHTS_EXPRESSION_SYNTAX')
            name+=' WITH '+exception.lower();cursor+=1
        return ('ATOM',name)
    def conjunction(depth):
        nonlocal cursor
        n=atom(depth)
        while cursor<len(tokens) and tokens[cursor]=='AND':
            cursor+=1;n=('AND',n,atom(depth))
        return n
    def disjunction(depth):
        nonlocal cursor
        n=conjunction(depth)
        while cursor<len(tokens) and tokens[cursor]=='OR':
            cursor+=1;n=('OR',n,conjunction(depth))
        return n
    n=disjunction(0)
    if cursor!=len(tokens):raise ContractError('RIGHTS_EXPRESSION_SYNTAX')
    return n

def single_atom(expression):
    n=parse(expression)
    if n[0]!='ATOM':raise ContractError('RIGHTS_GRANT_SINGLE_ATOM_REQUIRED')
    return n[1]

def selected_branch(expression, selections):
    """Require exactly one complete selection, not unbound or partial leaf claims."""
    tree=parse(expression)
    if type(selections) is not tuple or not selections:raise ContractError('RIGHTS_EMPTY_LICENSE_SELECTION')
    chosen=tuple(single_atom(x) for x in selections)
    if len(set(chosen))!=len(chosen):raise ContractError('RIGHTS_DUPLICATE_LICENSE_SELECTION')
    present=set(chosen)
    def walk(n):
        if n[0]=='ATOM':return {n[1]} if n[1] in present else None
        a,b=walk(n[1]),walk(n[2])
        if n[0]=='AND':return a|b if a is not None and b is not None else None
        if a is not None and b is not None:
            if a!=b:raise ContractError('RIGHTS_AMBIGUOUS_OR_SELECTION')
            return a
        return a if a is not None else b
    used=walk(tree)
    if used is None or used!=present:raise ContractError('RIGHTS_LICENSE_SELECTION_INCOMPLETE')
    return tuple(sorted(used))
