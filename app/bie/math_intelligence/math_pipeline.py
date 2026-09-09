from dataclasses import dataclass
import re
@dataclass(frozen=True)
class MathArtifact:
 source:str; expression:str; tokens:tuple[str,...]; symbols:tuple[str,...]; relation:str|None; qa:tuple[str,...]
def process_math(expression:str,source:str)->MathArtifact:
 if not source.strip(): raise ValueError("source provenance required")
 e=(expression or "").strip()
 if not e: raise ValueError("empty expression")
 toks=tuple(re.findall(r"\\[A-Za-z]+|\d+(?:\.\d+)?|[A-Za-zα-ωΑ-Ω]+|<=|>=|!=|[+\-*/=^_(),{}\[\]<>]|[^\s]",e))
 syms=tuple(sorted(set(t for t in toks if re.fullmatch(r"[A-Za-zα-ωΑ-Ω]+",t))))
 rel=next((r for r in ("<=",">=","!=","=","<",">","≈") if r in e),None)
 qa=[]
 if rel is None: qa.append("no_relation")
 depth=0
 for t in toks:
  if t in ("(","[","{"): depth+=1
  elif t in (")","]","}"): depth-=1
  if depth<0: qa.append("delimiter_error");break
 if depth: qa.append("delimiter_error")
 return MathArtifact(source,e,toks,syms,rel,tuple(dict.fromkeys(qa)))
