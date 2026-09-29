"""HARD015: additive complete parser using the native Node contract.

The native parser is preserved. No token can be silently discarded. Operators
are explicit; unknown syntax, implicit multiplication and oversized inputs fail.
"""
from __future__ import annotations
import re
from dataclasses import asdict
from ...math_intelligence.expression_ast import Node, parse_expression as legacy_parse
from ..math_v2.expression import parse as strict_parse, Expr, num, SYM, render
from .common import require,ContractError,digest,rational
LEX=re.compile(r'\s*(?:(\d+(?:\.\d+)?|\.\d+)([eE][+-]?\d+)?|([A-Za-z][A-Za-z0-9_]*)|(\*\*|[()+*/^,-]))')

def tokenize(value):
    require(type(value)is str and 0<len(value.strip())<=2048,'PARSER_TEXT')
    value=value.strip();out=[];pos=0
    while pos<len(value):
        m=LEX.match(value,pos);require(m is not None,'PARSER_UNKNOWN_CHARACTER')
        out.append((m[1]+(m[2]or''))if m[1]else(m[3]or m[4]));pos=m.end()
        require(len(out)<=256,'PARSER_TOKEN_LIMIT')
    return out

def parse_complete(tokens):
    require(type(tokens)is list and 0<len(tokens)<=256,'PARSER_TOKEN_INVENTORY')
    for t in tokens:
        require(type(t)is str and t==t.strip() and tokenize(t)==[t],'PARSER_TOKEN_NOT_ATOMIC')
    i=0;count=0
    def expr(bp=0,depth=0):
        nonlocal i,count
        require(depth<24 and i<len(tokens),'PARSER_DEPTH_OR_OPERAND')
        t=tokens[i];i+=1;count+=1;require(count<=128,'PARSER_NODE_LIMIT')
        if t in ('+','-'): left=Node('unary',t,(expr(25,depth+1),))
        elif t=='(':
            left=expr(0,depth+1);require(i<len(tokens) and tokens[i]==')','PARSER_PARENTHESIS');i+=1
        elif SYM.fullmatch(t):left=Node('atom',t)
        else:
            rational(t);left=Node('atom',t)
        prec={'+':10,'-':10,'*':20,'/':20,'^':30,'**':30}
        while i<len(tokens)and tokens[i]in prec and prec[tokens[i]]>=bp:
            op=tokens[i];i+=1;p=prec[op]
            right=expr(p if op in ('^','**')else p+1,depth+1)
            left=Node('binary','^'if op=='**'else op,(left,right));count+=1
            require(count<=128,'PARSER_NODE_LIMIT')
        return left
    result=expr();require(i==len(tokens),'PARSER_UNCONSUMED_TOKENS')
    return result

def node_text(n,depth=0):
    require(type(n)is Node and depth<24 and type(n.children)is tuple,'PARSER_NODE_TYPE')
    if n.kind=='atom':
        require(not n.children and tokenize(n.value)==[n.value],'PARSER_ATOM');return n.value
    if n.kind=='unary':
        require(n.value in ('+','-')and len(n.children)==1,'PARSER_UNARY')
        return '('+n.value+node_text(n.children[0],depth+1)+')'
    require(n.kind=='binary'and n.value in ('+','-','*','/','^')and len(n.children)==2,'PARSER_BINARY')
    return '('+node_text(n.children[0],depth+1)+n.value+node_text(n.children[1],depth+1)+')'

def checked_expression(value):
    node=parse_complete(tokenize(value))
    # The separate inherited strict parser is an independent full-consumption oracle.
    result=strict_parse(node_text(node));require(result==strict_parse(value),'PARSER_ORACLE_MISMATCH')
    return result

def inspect_parser(value):
    tokens=tokenize(value);new=parse_complete(tokens)
    try:old=legacy_parse(tokens);old_payload=asdict(old);mismatch=old!=new
    except (ValueError,TypeError,IndexError):old_payload=None;mismatch=True
    return dict(original_text=value,complete_ast=asdict(new),roundtrip=node_text(new),
        native_ast=old_payload,native_mismatch=mismatch,complete_digest=digest(asdict(new)),
        native_overwritten=False,release_authorized=False,product_accepted=False)


from dataclasses import dataclass
from .common import PolicyDigest,ids,integer,read_input,items,unique,fields,finish,Finding

@dataclass(frozen=True)
class ParserPolicy(PolicyDigest):
    required_ids: tuple[str,...]
    max_cases: int=128
    def __post_init__(self):
        ids(self.required_ids,'PARSER_CASE');integer(self.max_cases,'max_cases',1,128)

def evaluate_parser(ref,root,binding,policy):
    data=read_input(root,ref,binding,policy,'BIE-QA-HARD-015',('expressions',))
    rows=unique(items(data['expressions'],'PARSER_EXPRESSIONS',1,policy.max_cases),'case_id','PARSER_CASE_DUPLICATE')
    require(set(rows)==set(policy.required_ids),'PARSER_CASE_CENSUS')
    out={};findings=[]
    for case,row in rows.items():
        fields(row,('case_id','text'));out[case]=inspect_parser(row['text'])
        require(parse_complete(tokenize(out[case]['roundtrip']))==parse_complete(tokenize(row['text'])),'PARSER_ROUNDTRIP')
        if out[case]['native_mismatch']:
            findings.append(Finding('NATIVE_PARSER_UNSAFE_WITHOUT_COMPLETE_ADAPTER',case))
    return finish('BIE-QA-HARD-015',binding,findings,(ref,),out)
