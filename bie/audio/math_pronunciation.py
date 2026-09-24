"""AUDIO-VO-003: bounded structural math-to-speech, without eval/CAS or rewriting.

Grammar v1: numeric literals, single Latin/declared Greek identifiers, groups,
+ - * /, relation, powers/subscripts, frac/sqrt/vector and grouped sin/cos/tan/log/ln/exp.
Unsupported or ambiguous notation is reported; it is never silently guessed.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from .common import AudioError, Reading, fingerprint, locale, refs, text
from .common import EN, HI

GREEK={"alpha":("alpha","अल्फा"),"beta":("beta","बीटा"),"gamma":("gamma","गामा"),"delta":("delta","डेल्टा"),
       "theta":("theta","थीटा"),"lambda":("lambda","लैम्ब्डा"),"mu":("mu","म्यू"),"pi":("pi","पाई"),
       "rho":("rho","रो"),"sigma":("sigma","सिग्मा"),"phi":("phi","फाई"),"omega":("omega","ओमेगा")}
UNICODE_GREEK=dict(zip("αβγδθλμπρσφω",GREEK))
OPS={"+":"+","-":"-","−":"-","*":"*","×":"*","/":"/","÷":"/","=":"=","<":"<",">":">","≤":"<=","≥":">=","≠":"!=","≈":"approx","±":"+-"}
COMMANDS={"times":"*","cdot":"*","div":"/","le":"<=","leq":"<=","ge":">=","geq":">=","ne":"!=","neq":"!=","approx":"approx","pm":"+-"}
RELATIONS={"=","<",">","<=",">=","!=","approx"}
FUNCS={"sin","cos","tan","log","ln","exp"}


@dataclass(frozen=True)
class Token:
    value: str
    start: int
    end: int
    kind: str


@dataclass(frozen=True)
class MathNode:
    kind: str
    value: str
    children: tuple[MathNode,...]
    start: int
    end: int


@dataclass(frozen=True)
class MathRealization:
    expression: str
    ast: MathNode
    reading: Reading
    grammar_version: str = "bie-math-reading/1"
    mathematical_validity_verified: bool = False
    audio_verified: bool = False

    def fingerprint(self):return fingerprint(self)


def tokenize(expression: str) -> tuple[Token,...]:
    text(expression,"math",4096)
    out=[];i=0
    while i<len(expression):
        c=expression[i]
        if c.isspace():i+=1;continue
        start=i
        if expression[i:i+2] in ("<=",">=","!="):
            value=expression[i:i+2];i+=2;kind="OP"
        elif c=="\\":
            m=re.match(r"\\([A-Za-z]+)",expression[i:])
            if not m:raise AudioError("UNSUPPORTED_MATH_ESCAPE",str(i))
            word=m.group(1);i+=len(m.group())
            if word in GREEK:kind,value="IDENT",word
            elif word in COMMANDS:kind,value="OP",COMMANDS[word]
            elif word in {"frac","sqrt","vec"}|FUNCS:kind,value="COMMAND",word
            else:raise AudioError("UNSUPPORTED_MATH_COMMAND",word)
        elif c.isascii() and c.isdigit():
            m=re.match(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?",expression[i:]);value=m.group();i+=len(value);kind="NUMBER"
            if len(value)>64:raise AudioError("MATH_NUMBER_BUDGET")
        elif c in UNICODE_GREEK:value=UNICODE_GREEK[c];kind="IDENT";i+=1
        elif c.isascii() and c.isalpha():
            m=re.match(r"[A-Za-z]+",expression[i:]);value=m.group();i+=len(value);kind="IDENT"
            if len(value)!=1:raise AudioError("MULTILETTER_SYMBOL_NEEDS_EXPLICIT_READING",value)
        elif c in OPS:value=OPS[c];kind="OP";i+=1
        elif c in "(){}^_":value=c;kind="DELIMITER";i+=1
        else:raise AudioError("UNSUPPORTED_MATH_TOKEN",f"{i}:{c}")
        out.append(Token(value,start,i,kind))
        if len(out)>512:raise AudioError("MATH_TOKEN_BUDGET")
    if not out:raise AudioError("EMPTY_MATH")
    return tuple(out)


class Parser:
    def __init__(self,tokens):self.tokens=tokens;self.i=0
    def peek(self):return self.tokens[self.i] if self.i<len(self.tokens) else None
    def take(self):
        t=self.peek()
        if t is None:raise AudioError("MATH_UNEXPECTED_END")
        self.i+=1;return t
    def grouped(self,depth,expected=None):
        left=self.take()
        if left.value not in ("(","{") or (expected and left.value!=expected):raise AudioError("MATH_GROUP_REQUIRED")
        inner=self.expr(0,depth+1);right=self.take()
        if right.value!= (")" if left.value=="(" else "}"):raise AudioError("MATH_UNBALANCED_GROUP")
        return MathNode("group",left.value,(inner,),left.start,right.end)
    def script(self,depth):
        p=self.peek()
        if not p:raise AudioError("MATH_UNEXPECTED_END")
        if p.value in ("{","("):return self.grouped(depth)
        if p.kind not in ("NUMBER","IDENT"):raise AudioError("MATH_SCRIPT_GROUP_REQUIRED")
        if p.kind=="NUMBER" and len(p.value)!=1:raise AudioError("MATH_SCRIPT_GROUP_REQUIRED")
        self.take();return MathNode("number" if p.kind=="NUMBER" else "symbol",p.value,(),p.start,p.end)
    def expr(self,bp=0,depth=0):
        if depth>32:raise AudioError("MATH_DEPTH_BUDGET")
        p=self.peek()
        if p is None:raise AudioError("MATH_UNEXPECTED_END")
        if p.value in ("(","{"):lhs=self.grouped(depth)
        else:
            t=self.take()
            if t.kind in ("NUMBER","IDENT"):
                lhs=MathNode("number" if t.kind=="NUMBER" else "symbol",t.value,(),t.start,t.end)
            elif t.value in ("+","-"):
                child=self.expr(25,depth+1);lhs=MathNode("unary",t.value,(child,),t.start,child.end)
            elif t.kind=="COMMAND":
                if t.value=="frac":
                    a=self.grouped(depth,"{");b=self.grouped(depth,"{");lhs=MathNode("fraction","/",(a,b),t.start,b.end)
                else:
                    a=self.grouped(depth,"{" if t.value in ("sqrt","vec") else None)
                    lhs=MathNode("function",t.value,(a,),t.start,a.end)
            else:raise AudioError("MATH_OPERAND_REQUIRED",t.value)
        while self.peek():
            t=self.peek()
            if t.value in ("}",")"):break
            if t.value in ("^","_"):
                if 35<bp:break
                self.take();rhs=self.script(depth+1)
                if lhs.kind=="script" and lhs.value==t.value:raise AudioError("DUPLICATE_MATH_SCRIPT")
                lhs=MathNode("script",t.value,(lhs,rhs),lhs.start,rhs.end);continue
            op=t.value
            power=5 if op in RELATIONS else 10 if op in ("+","-","+-") else 20 if op in ("*","/") else -1
            if power<0:
                # Only numeric juxtaposition before a symbol/group is supported.
                if lhs.kind=="number" and (t.kind=="IDENT" or t.value=="("):
                    if 20<bp:break
                    rhs=self.expr(21,depth+1);lhs=MathNode("binary","*",(lhs,rhs),lhs.start,rhs.end);continue
                raise AudioError("AMBIGUOUS_MATH_JUXTAPOSITION",t.value)
            if power<bp:break
            if op in RELATIONS and lhs.kind=="binary" and lhs.value in RELATIONS:raise AudioError("MATH_RELATION_CHAIN_REQUIRES_SCOPE")
            self.take();rhs=self.expr(power+1,depth+1)
            lhs=MathNode("fraction" if op=="/" else "binary",op,(lhs,rhs),lhs.start,rhs.end)
        return lhs


def parse_math(expression: str) -> MathNode:
    p=Parser(tokenize(expression));node=p.expr()
    if p.peek():raise AudioError("MATH_TRAILING_INPUT",p.peek().value)
    return node

ONES=("zero","one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen")
HINDI=("शून्य","एक","दो","तीन","चार","पाँच","छह","सात","आठ","नौ","दस","ग्यारह","बारह","तेरह","चौदह","पंद्रह","सोलह","सत्रह","अठारह","उन्नीस","बीस")
TENS=("","","twenty","thirty","forty","fifty","sixty","seventy","eighty","ninety")

def cardinal(n):
    if n<20:return ONES[n]
    if n<100:return TENS[n//10]+(" "+ONES[n%10] if n%10 else "")
    for value,name in ((1000000,"million"),(1000,"thousand"),(100,"hundred")):
        if n>=value:return cardinal(n//value)+" "+name+(" "+cardinal(n%value) if n%value else "")
    raise AudioError("NUMBER_OUTSIDE_READING")

def number_words(value,lang):
    if "e" in value.lower():
        mantissa,exponent=re.split('[eE]',value)
        sign="negative " if exponent.startswith('-') else ""
        if lang=='hi':sign="ऋण " if exponent.startswith('-') else ""
        exp=number_words(exponent.lstrip('+-'),lang)
        return number_words(mantissa,lang)+(f" times ten to the power {sign}{exp} end power" if lang=='en' else f" गुणा दस की घात {sign}{exp} घात समाप्त")
    whole,sep,fraction=value.partition('.')
    n=int(whole)
    if whole.startswith('0') and len(whole)>1 or n>999999999 or lang=='hi' and n>20:
        spoken=("digits " if lang=='en' else "अंक ")+" ".join((ONES if lang=='en' else HINDI)[int(x)] for x in whole)
    else:spoken=cardinal(n) if lang=='en' else HINDI[n]
    if sep:spoken+=(" point " if lang=='en' else " दशमलव ")+" ".join((ONES if lang=='en' else HINDI)[int(x)] for x in fraction)
    return spoken


def speak_node(node:MathNode,lang:str) -> str:
    def read(n):return speak_node(n,lang)
    def ungroup(n):return n.children[0] if n.kind=='group' else n
    if node.kind=='number':return number_words(node.value,lang)
    if node.kind=='symbol':
        if node.value in GREEK:return GREEK[node.value][0 if lang=='en' else 1]
        if len(node.value)==1 and node.value.isascii() and node.value.isalpha():
            return ("capital " if lang=='en' else "बड़ा ")*(node.value.isupper())+(node.value.lower() if lang=='en' else HI[ord(node.value.upper())-65])
        raise AudioError('MATH_SYMBOL_READING_MISSING',node.value)
    if node.kind=='group':return ("open parenthesis " if lang=='en' else "कोष्ठक शुरू ")+read(node.children[0])+(" close parenthesis" if lang=='en' else " कोष्ठक समाप्त")
    if node.kind=='unary':return ({'+':'positive ','-':'negative '} if lang=='en' else {'+':'धन ','-':'ऋण '})[node.value]+read(node.children[0])
    if node.kind=='fraction':
        a,b=(read(ungroup(x)) for x in node.children)
        return f"start fraction numerator {a} denominator {b} end fraction" if lang=='en' else f"भिन्न शुरू अंश {a} हर {b} भिन्न समाप्त"
    if node.kind=='script':
        a,b=node.children;b=ungroup(b)
        if node.value=='^' and b.kind=='number' and b.value in ('2','3'):
            return read(a)+({'2':' squared','3':' cubed'} if lang=='en' else {'2':' का वर्ग','3':' का घन'})[b.value]
        return read(a)+((" to the power " if node.value=='^' else " subscript ") if lang=='en' else (" की घात " if node.value=='^' else " अधोलिखित "))+read(b)+((" end power" if node.value=='^' else " end subscript") if lang=='en' else " समाप्त")
    if node.kind=='function':
        a=read(ungroup(node.children[0]));f=node.value
        if f=='sqrt':return f"square root of {a} end root" if lang=='en' else f"वर्गमूल शुरू {a} वर्गमूल समाप्त"
        if f=='vec':return f"vector {a}" if lang=='en' else f"सदिश {a}"
        names={'sin':('sine','साइन'),'cos':('cosine','कोसाइन'),'tan':('tangent','टैन्जेंट'),'ln':('natural logarithm','प्राकृतिक लघुगणक'),'log':('logarithm','लघुगणक'),'exp':('exponential function','एक्सपोनेंशियल फलन')}
        name=names[f][0 if lang=='en' else 1]
        return f"{name} of {a} end function" if lang=='en' else f"{name} का तर्क {a} फलन समाप्त"
    if node.kind=='binary':
        en={'+':'plus','-':'minus','*':'times','=':'equals','<':'less than','>':'greater than','<=':'less than or equal to','>=':'greater than or equal to','!=':'not equal to','approx':'approximately equals','+-':'plus or minus'}
        hi={'+':'धन','-':'ऋण','*':'गुणा','=':'बराबर','<':'से छोटा','>':'से बड़ा','<=':'से छोटा या बराबर','>=':'से बड़ा या बराबर','!=':'के बराबर नहीं','approx':'लगभग बराबर','+-':'धन या ऋण'}
        a,b=read(node.children[0]),read(node.children[1])
        if lang=='hi' and node.value in ('<','>','<=','>=','!='):
            return a+", "+b+" "+hi[node.value]+" है"
        return a+" "+(en if lang=='en' else hi)[node.value]+" "+b
    raise AudioError('UNKNOWN_MATH_NODE')


def pronounce_math(expression: str, language: str = "en", *, evidence_refs: tuple[str,...] = ("bie:audio:math-reading-conventions:1",)) -> MathRealization:
    locale(language);refs(evidence_refs,'math source evidence')
    lang=language.split('-')[0]
    if lang not in ('en','hi'):raise AudioError('MATH_LANGUAGE_NOT_SUPPORTED',language)
    ast=parse_math(expression)
    spoken=speak_node(ast,lang)
    r=Reading(expression,spoken,language,'MATH','bie-math-reading/1',evidence_refs)
    return MathRealization(expression,ast,r)
